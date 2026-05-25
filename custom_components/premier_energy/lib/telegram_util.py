"""Notificări Telegram — Premier Energy."""

from __future__ import annotations

import logging
from pathlib import Path

import requests

_LOGGER = logging.getLogger(__name__)


def send_telegram(token: str, chat_id: str, message: str) -> bool:
    if not token or not chat_id:
        _LOGGER.debug("Telegram not configured for Premier")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": message[:4000]},
            timeout=30,
        )
        if r.status_code != 200:
            _LOGGER.error("Telegram HTTP %s: %s", r.status_code, r.text[:200])
        return r.status_code == 200
    except Exception as exc:
        _LOGGER.error("Telegram error: %s", exc)
        return False


def send_telegram_document(
    token: str,
    chat_id: str,
    pdf_path: Path,
    caption: str = "",
) -> bool:
    if not token or not chat_id:
        _LOGGER.warning("Telegram not configured")
        return False
    if not pdf_path.is_file():
        _LOGGER.error("PDF lipsă: %s", pdf_path)
        return False
    try:
        with pdf_path.open("rb") as pdf:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendDocument",
                data={
                    "chat_id": chat_id,
                    "caption": caption[:1024],
                    "disable_notification": False,
                },
                files={"document": pdf},
                timeout=90,
            )
        if r.status_code != 200:
            _LOGGER.error("Telegram document HTTP %s: %s", r.status_code, r.text[:300])
        return r.status_code == 200
    except Exception as exc:
        _LOGGER.error("Telegram document error: %s", exc)
        return False
