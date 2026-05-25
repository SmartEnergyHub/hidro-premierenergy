"""Trimite ultima factură Hidroelectrica pe Telegram (sync — executor)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .api_client import download_invoice_pdf
from .config import DATA_FILE
from .ha_session import ensure_session
from .hidro_api import fetch_all_portal_data, get_billing_history, load_page, parse_billing_rows
from .logging_util import setup_logger
from .session import requests_session_from_store, validate_session
from .telegram_util import send_telegram_document

log = setup_logger("hidro.send_invoice_tg")


def _latest_invoice(http) -> dict[str, Any]:
    html, csrf = load_page(http, "billing")
    rows = get_billing_history(http, csrf, tab_type="menu1")
    invoices = parse_billing_rows(rows)
    if invoices:
        return invoices[0]
    data = fetch_all_portal_data(http)
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    ultima = data.get("ultima_factura") or {}
    if ultima.get("numar"):
        return ultima
    facturi = data.get("facturi") or []
    if facturi:
        return facturi[0]
    raise RuntimeError("NU_EXISTA_FACTURI")


def send_last_invoice_telegram_sync(
    *,
    telegram_bot_token: str = "",
    telegram_chat_id: str = "",
) -> str:
    if not telegram_bot_token or not telegram_chat_id:
        raise RuntimeError("Telegram neconfigurat în integrarea Hidroelectrica")

    if not ensure_session():
        raise RuntimeError("SESIUNE_EXPIRATA — apasă Re-login forțat")

    http = requests_session_from_store()
    if not validate_session(http, touch=False):
        raise RuntimeError("Sesiune invalidă")

    inv = _latest_invoice(http)
    numar = inv.get("numar") or inv.get("Numar") or inv.get("invoice_number")
    if not numar:
        raise RuntimeError("Număr factură lipsă")

    enc = inv.get("EncryptedData") or inv.get("encrypted_data")
    pdf_path = download_invoice_pdf(str(numar), enc_query=enc)
    if not pdf_path:
        raise RuntimeError(f"PDF indisponibil pentru {numar}")

    suma = inv.get("suma") or inv.get("total") or "—"
    scadenta = inv.get("scadenta") or inv.get("data_scadenta") or "—"
    caption = (
        "⚡ FACTURA HIDROELECTRICA\n\n"
        f"💰 Sumă: {suma}\n"
        f"📅 Scadență: {scadenta}\n\n"
        f"📄 Factura: {numar}"
    )
    if not send_telegram_document(
        telegram_bot_token,
        telegram_chat_id,
        Path(pdf_path),
        caption,
    ):
        raise RuntimeError("Trimitere Telegram eșuată")
    log.info("Factură %s trimisă pe Telegram", numar)
    return str(numar)
