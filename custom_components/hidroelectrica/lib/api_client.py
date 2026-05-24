"""Client fetch date Hidroelectrica."""

from __future__ import annotations

import json
from typing import Any

from .backup import backup_files
from .config import DATA_FILE, INVOICES_DIR, PORTAL_BASE, PORTAL_PAGES
from .hidro_api import fetch_all_portal_data, load_page
from .logging_util import setup_logger
from .session import extract_csrf_from_html, requests_session_from_store, validate_session

log = setup_logger("hidro.api")


def fetch_all_data(use_browser: bool = False) -> dict[str, Any]:
    if DATA_FILE.is_file():
        backup_files([DATA_FILE], label="pre_data_fetch")

    http = requests_session_from_store()
    if not validate_session(http):
        raise RuntimeError("Sesiune invalidă — rulează import_session.py cu cookies noi")

    data = fetch_all_portal_data(http)
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("data.json updated — POD=%s facturi=%d", data.get("pod"), len(data.get("facturi", [])))
    return data


def _pdf_token_for_invoice(data: dict[str, Any], invoice_id: str) -> str | None:
    ultima = data.get("ultima_factura") or {}
    if str(ultima.get("numar")) == str(invoice_id) and ultima.get("pdf_token"):
        return str(ultima["pdf_token"])
    for inv in data.get("facturi") or []:
        if str(inv.get("numar")) == str(invoice_id) and inv.get("pdf_token"):
            return str(inv["pdf_token"])
    return None


def _ajax_headers(csrf: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json; charset=utf-8",
        "csrftoken": csrf,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{PORTAL_BASE}/{PORTAL_PAGES['billing']}",
    }


def download_invoice_pdf(invoice_id: str, enc_query: str | None = None) -> str | None:
    http = requests_session_from_store()
    if not validate_session(http):
        raise RuntimeError("Sesiune invalidă")

    token = enc_query
    if not token and DATA_FILE.is_file():
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        token = _pdf_token_for_invoice(data, invoice_id)

    if not token:
        log.error("Lipsește EncryptedData pentru factura %s", invoice_id)
        return None

    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    dest = INVOICES_DIR / f"factura_{invoice_id}.pdf"

    try:
        _, csrf = load_page(http, "billing")
    except Exception:
        csrf = extract_csrf_from_html(
            http.get(f"{PORTAL_BASE}/{PORTAL_PAGES['billing']}", timeout=60).text
        )

    r = http.post(
        f"{PORTAL_BASE}/BillDashboard.aspx/GetPaymentOverDueRemainderPDF",
        json={"EncQuery": token},
        headers=_ajax_headers(csrf),
        timeout=60,
    )
    r.raise_for_status()
    raw = r.json().get("d", "")
    if not raw:
        log.error("PDF API fără răspuns pentru %s", invoice_id)
        return None

    file_ref = json.loads(raw) if isinstance(raw, str) and raw.startswith('"') else raw
    if not isinstance(file_ref, str):
        log.error("PDF API format neașteptat: %s", type(file_ref))
        return None

    upload_path, _, filename = file_ref.partition(",")
    upload_path = upload_path.strip()
    if not upload_path.startswith("http"):
        upload_path = f"{PORTAL_BASE}/{upload_path.lstrip('/')}"

    pdf = http.get(upload_path, timeout=90)
    pdf.raise_for_status()
    if b"%PDF" not in pdf.content[:16]:
        log.error("Răspuns non-PDF de la %s", upload_path)
        return None

    dest.write_bytes(pdf.content)
    log.info("PDF salvat %s (%d bytes)", dest, len(pdf.content))
    return str(dest)
