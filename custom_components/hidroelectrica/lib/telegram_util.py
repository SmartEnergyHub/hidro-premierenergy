"""Notificări Telegram."""

from __future__ import annotations

from pathlib import Path

import requests

from .logging_util import setup_logger

log = setup_logger("hidro.telegram")


def send_telegram(token: str, chat_id: str, message: str) -> bool:
    if not token or not chat_id:
        log.warning("Telegram not configured")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": message[:4000]},
            timeout=30,
        )
        ok = r.status_code == 200
        if not ok:
            log.error("Telegram HTTP %s: %s", r.status_code, r.text[:200])
        return ok
    except Exception as exc:
        log.error("Telegram error: %s", exc)
        return False


def send_telegram_document(
    token: str,
    chat_id: str,
    pdf_path: Path,
    caption: str = "",
) -> bool:
    if not token or not chat_id:
        log.warning("Telegram not configured")
        return False
    if not pdf_path.is_file():
        log.error("PDF lipsă: %s", pdf_path)
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
        ok = r.status_code == 200
        if not ok:
            log.error("Telegram document HTTP %s: %s", r.status_code, r.text[:300])
        return ok
    except Exception as exc:
        log.error("Telegram document error: %s", exc)
        return False
