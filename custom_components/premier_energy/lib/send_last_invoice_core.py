"""Trimite ultima factură Premier Energy pe Telegram (sync — executor)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import requests

from ..const import API_BASE
from .api_client import PremierApiClient
from .auth_manager import PremierAuthManager
from .telegram_util import send_telegram, send_telegram_document

_LOGGER = logging.getLogger(__name__)


def _load_telegram(secrets_dir: Path) -> tuple[str, str]:
    secrets_file = secrets_dir / "secrets.json"
    if not secrets_file.is_file():
        return "", ""
    try:
        data = json.loads(secrets_file.read_text(encoding="utf-8"))
        return (
            (data.get("telegram_bot_token") or "").strip(),
            (data.get("telegram_chat_id") or "").strip(),
        )
    except Exception:
        return "", ""


def send_last_invoice_telegram_sync(
    auth: PremierAuthManager,
    invoices_dir: Path,
    *,
    coordinator_data: dict | None = None,
    secrets_dir: Path | None = None,
    telegram_bot_token: str = "",
    telegram_chat_id: str = "",
) -> str:
    """Reînnoiește tokenul, descarcă PDF ultima factură, trimite pe Telegram."""
    if secrets_dir and not (telegram_bot_token and telegram_chat_id):
        telegram_bot_token, telegram_chat_id = _load_telegram(secrets_dir)
    if not telegram_bot_token or not telegram_chat_id:
        raise RuntimeError("Telegram neconfigurat (secrets.json sau integrare)")

    token = auth.read_token()
    if not token or not auth.token_is_valid(token, margin=120):
        token = auth.refresh_token()
    elif not auth.validate_token_via_api(token):
        token = auth.refresh_token()
    client = PremierApiClient(token)
    data = coordinator_data if coordinator_data and coordinator_data.get("numar_factura") else client.fetch_all()

    numar = data.get("numar_factura")
    if not numar:
        raise RuntimeError("NU_EXISTA_FACTURI")

    pdf_path = client.download_invoice_pdf(str(numar), invoices_dir)
    if not pdf_path:
        raise RuntimeError(f"PDF indisponibil pentru factura {numar}")

    suma = data.get("ultima_factura_suma") or "—"
    scadenta = data.get("scadenta") or "—"
    consum_m3 = data.get("consum_m3") or "—"
    consum_mwh = data.get("consum_mwh") or "—"
    caption = (
        "🔥 FACTURA GAZE PREMIER\n\n"
        f"💰 Sumă: {suma} RON\n"
        f"📅 Scadență: {scadenta}\n\n"
        f"📊 Consum:\n• {consum_m3} m³\n• {consum_mwh} MWh\n\n"
        f"📄 Factura: {numar}"
    )
    if not send_telegram_document(
        telegram_bot_token, telegram_chat_id, Path(pdf_path), caption
    ):
        raise RuntimeError("Trimitere Telegram eșuată")
    return str(numar)
