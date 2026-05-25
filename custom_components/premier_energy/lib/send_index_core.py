"""Transmitere index autocitire Premier Energy (sync — rulează în executor)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from ..const import API_BASE
from .telegram_util import send_telegram

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


def _loc_payload(coordinator_data: dict[str, Any] | None) -> dict[str, str]:
    locuri = (coordinator_data or {}).get("locuri") or []
    loc = locuri[0] if locuri else {}
    loc_consum = (
        loc.get("LocConsum")
        or loc.get("locConsum")
        or loc.get("CodLocConsum")
        or ""
    )
    contract = str(loc.get("Contract") or loc.get("contract") or loc.get("NumarContract") or "")
    if not loc_consum or not contract:
        raise RuntimeError("locConsum/contract lipsesc — rulează Refresh Premier Energy")
    return {
        "index": "",
        "locConsum": str(loc_consum),
        "sursa": "portalClienti",
        "contract": contract,
    }


def send_index_sync(
    index: int,
    token: str,
    coordinator_data: dict[str, Any] | None,
    *,
    secrets_dir: Path | None = None,
    telegram_bot_token: str = "",
    telegram_chat_id: str = "",
) -> str:
    if index <= 0:
        raise ValueError("Index invalid — completează input_number.index_gaz_premier")

    payload = _loc_payload(coordinator_data)
    payload["index"] = str(index)
    headers = {"Premier-Auth": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE}/index"
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    body = r.text[:500]

    if secrets_dir and not (telegram_bot_token and telegram_chat_id):
        telegram_bot_token, telegram_chat_id = _load_telegram(secrets_dir)

    if r.status_code == 200:
        msg = f"✅ Index gaze Premier trimis\n\n🔢 Index: {index}\n📨 Răspuns: {body}"
    else:
        msg = f"❌ Eroare index gaze Premier\n\n🔢 Index: {index}\nHTTP: {r.status_code}\n{body}"
        send_telegram(telegram_bot_token, telegram_chat_id, msg)
        raise RuntimeError(f"Premier index HTTP {r.status_code}: {body}")

    send_telegram(telegram_bot_token, telegram_chat_id, msg)
    _LOGGER.info("Premier index trimis: %s", index)
    return body
