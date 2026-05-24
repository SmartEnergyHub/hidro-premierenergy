"""API iHidro — CSRF + WebMethods + parsare HTML."""

from __future__ import annotations

import json
import re
from typing import Any

import requests

from .config import API_ENDPOINTS, PORTAL_BASE, PORTAL_PAGES
from .logging_util import setup_logger
from .session import extract_csrf_from_html, is_login_page, requests_session_from_store

log = setup_logger("hidro.api_wm")


def _headers(csrf: str, referer: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json; charset=utf-8",
        "csrftoken": csrf,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": referer,
    }


def _date_key(text: str) -> str:
    parts = (text or "").strip().split("/")
    if len(parts) == 3:
        return parts[2] + parts[1] + parts[0]
    return text or ""


def load_page(sess: requests.Session, page_key: str) -> tuple[str, str]:
    path = PORTAL_PAGES[page_key]
    url = f"{PORTAL_BASE}/{path}"
    r = sess.get(url, timeout=60, allow_redirects=True)
    r.raise_for_status()
    if is_login_page(r.text, r.url):
        raise RuntimeError(f"Sesiune expirată la {path} — Re-login forțat în HA")
    csrf = extract_csrf_from_html(r.text)
    return r.text, csrf


def post_webmethod(
    sess: requests.Session,
    endpoint: str,
    payload: dict[str, Any],
    csrf: str,
    referer_page: str,
) -> Any:
    url = f"{PORTAL_BASE}/{endpoint}"
    referer = f"{PORTAL_BASE}/{referer_page}"
    r = sess.post(url, json=payload, headers=_headers(csrf, referer), timeout=60)
    r.raise_for_status()
    outer = r.json()
    raw = outer.get("d", outer)
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


def get_pods(sess: requests.Session, csrf: str) -> list[dict[str, Any]]:
    data = post_webmethod(sess, API_ENDPOINTS["pods"], {}, csrf, PORTAL_PAGES["index_history"])
    if isinstance(data, dict) and data.get("Data"):
        return data["Data"]
    if isinstance(data, list) and data and str(data[0].get("StatusCode")) == "0":
        raise RuntimeError(data[0].get("MessageInformation", "API POD eșuat"))
    return []


def get_index_history(
    sess: requests.Session, csrf: str, installation: str, pod: str
) -> list[dict[str, Any]]:
    payload = {"installation": installation, "podvalue": pod}
    data = post_webmethod(
        sess, API_ENDPOINTS["index_grid"], payload, csrf, PORTAL_PAGES["index_history"]
    )
    return data if isinstance(data, list) else []


def get_billing_history(
    sess: requests.Session,
    csrf: str,
    tab_type: str = "menu1",
    from_date: str = "",
    to_date: str = "",
    invoice_type: str = "",
) -> list[dict[str, Any]]:
    payload = {
        "tabType": tab_type,
        "fromDate": from_date,
        "toDate": to_date,
        "invoiceType": invoice_type,
    }
    data = post_webmethod(
        sess,
        API_ENDPOINTS["billing_grid"],
        payload,
        csrf,
        PORTAL_PAGES["billing"],
    )
    return data if isinstance(data, list) else []


def _invoice_from_obj(obj: dict[str, Any]) -> dict[str, Any] | None:
    from .parsers import _clean_num, _iso_date

    num = str(obj.get("exbel") or obj.get("InvoiceNumber") or "").strip()
    if not num:
        return None
    amount = obj.get("Amount") or obj.get("amount") or obj.get("TotalAmount")
    due = obj.get("DBDueDate") or obj.get("DueDate") or obj.get("dueDate")
    issued = obj.get("Date") or obj.get("BillDate") or obj.get("IssueDate")
    return {
        "numar": num,
        "data_emitere": _iso_date(str(issued or "")),
        "scadenta": _iso_date(str(due or "")),
        "suma": _clean_num(str(amount or "")),
        "tip": str(obj.get("invoiceType") or obj.get("InvoiceType") or ""),
        "pdf_token": str(
            obj.get("EncryptedData") or obj.get("encryptedData") or obj.get("EncQuery") or ""
        ),
    }


def parse_invoices_embedded(html: str) -> list[dict[str, Any]]:
    invoices: list[dict[str, Any]] = []
    seen: set[str] = set()

    if '"exbel"' in html:
        for mobj in re.finditer(r'\{[^{}]*"exbel"\s*:\s*"[0-9]+"[^{}]*\}', html, re.I):
            try:
                obj = json.loads(mobj.group(0))
            except json.JSONDecodeError:
                continue
            inv = _invoice_from_obj(obj)
            if inv and inv["numar"] not in seen:
                seen.add(inv["numar"])
                invoices.append(inv)

        if not invoices:
            for num in re.findall(r'"exbel"\s*:\s*"(\d{8,14})"', html):
                if num in seen:
                    continue
                ctx = html[
                    max(0, html.find(f'"exbel":"{num}"') - 400) : html.find(f'"exbel":"{num}"')
                    + 800
                ]
                inv = {
                    "numar": num,
                    "data_emitere": "",
                    "scadenta": "",
                    "suma": None,
                    "tip": "",
                    "pdf_token": "",
                }
                m_amt = re.search(r'"Amount"\s*:\s*"([^"]+)"', ctx)
                m_due = re.search(r'"DBDueDate"\s*:\s*"([^"]+)"', ctx)
                m_date = re.search(r'"Date"\s*:\s*"([^"]+)"', ctx)
                m_tip = re.search(r'"invoiceType"\s*:\s*"([^"]+)"', ctx)
                m_pdf = re.search(r'"EncryptedData"\s*:\s*"([^"]+)"', ctx)
                from .parsers import _clean_num, _iso_date

                if m_amt:
                    inv["suma"] = _clean_num(m_amt.group(1))
                if m_due:
                    inv["scadenta"] = _iso_date(m_due.group(1))
                if m_date:
                    inv["data_emitere"] = _iso_date(m_date.group(1))
                if m_tip:
                    inv["tip"] = m_tip.group(1)
                if m_pdf:
                    inv["pdf_token"] = m_pdf.group(1)
                seen.add(num)
                invoices.append(inv)

    invoices.sort(key=lambda x: x.get("data_emitere") or "", reverse=True)
    return invoices


def parse_billing_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    invoices: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        inv = _invoice_from_obj(row)
        if inv and inv["numar"] not in seen:
            seen.add(inv["numar"])
            invoices.append(inv)
    invoices.sort(key=lambda x: x.get("data_emitere") or "", reverse=True)
    return invoices


def _to_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        s = str(val).strip().replace(",", "")
        return int(float(s)) if "." in s else int(s)
    except ValueError:
        return None


def _apply_index_rows(data: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    data["index_istoric"] = rows
    latest = max(rows, key=lambda r: _date_key(str(r.get("Date", ""))))
    data["index"]["curent"] = _to_int(latest.get("Index"))
    data["index"]["ultima_citire"] = latest.get("Date", "")
    data["index"]["tip_citire"] = latest.get("ReadingType", "")
    if latest.get("POD"):
        data["pod"] = latest.get("POD")


def fetch_all_portal_data(sess: requests.Session | None = None) -> dict[str, Any]:
    from .parsers import parse_portal_pages

    http = sess or requests_session_from_store()
    pages: dict[str, str] = {}
    csrf = ""

    for key in PORTAL_PAGES:
        try:
            html, csrf = load_page(http, key)
            pages[key] = html
            log.info("Loaded %s (%d bytes)", key, len(html))
        except Exception as exc:
            log.warning("Skip %s: %s", key, exc)

    if not pages:
        raise RuntimeError("Nicio pagină — sesiune invalidă, reimportă cookies")

    data = parse_portal_pages(pages)
    pod_info: dict[str, Any] = {}

    if csrf:
        try:
            pods = get_pods(http, csrf)
            if pods:
                pod_info = pods[0]
                data["pod"] = pod_info.get("pod") or data.get("pod", "")
                data["contract"] = str(
                    pod_info.get("contractAccountID") or data.get("contract", "")
                )
                rows = get_index_history(
                    http,
                    csrf,
                    str(pod_info.get("installation", "")),
                    str(pod_info.get("pod", "")),
                )
                _apply_index_rows(data, rows)
        except Exception as exc:
            log.warning("API index: %s", exc)

    invoices: list[dict[str, Any]] = []
    if csrf:
        try:
            rows = get_billing_history(http, csrf, tab_type="menu1")
            invoices = parse_billing_rows(rows)
            if not invoices:
                log.debug("billing menu1 empty, rows=%s", len(rows))
        except Exception as exc:
            log.warning("API billing: %s", exc)

    if not invoices and "billing" in pages:
        invoices = parse_invoices_embedded(pages["billing"])

    if invoices:
        data["facturi"] = invoices
        data["ultima_factura"] = invoices[0]
        if invoices[0].get("suma") is not None:
            data["sold"] = invoices[0]["suma"]

    data["session_valid"] = True
    return data
