#!/usr/bin/env python3
"""Trimite index gaze Premier + notificare Telegram."""
from __future__ import annotations

import json
import sys

import requests

from premier_session import API, ensure_token, headers, load_data, load_secrets, read_token, refresh_token


def _payload(index: int, data: dict) -> dict:
    locuri = data.get("locuri") or []
    loc = locuri[0] if locuri else {}
    loc_consum = loc.get("LocConsum") or loc.get("locConsum") or ""
    contract = str(loc.get("Contract") or loc.get("contract") or "")
    if not loc_consum or not contract:
        raise RuntimeError("locConsum/contract lipsesc — rulează integrarea Premier sau refresh data.json")
    return {
        "index": str(index),
        "locConsum": str(loc_consum),
        "sursa": "portalClienti",
        "contract": contract,
    }


def _notify(secrets: dict, text: str) -> None:
    bot = (secrets.get("telegram_bot_token") or "").strip()
    chat = (secrets.get("telegram_chat_id") or "").strip()
    if bot and chat and bot != "YOUR_TELEGRAM_BOT_TOKEN":
        requests.post(
            f"https://api.telegram.org/bot{bot}/sendMessage",
            data={"chat_id": chat, "text": text[:4000]},
            timeout=30,
        )


def main() -> int:
    if len(sys.argv) < 2 or not str(sys.argv[1]).strip():
        print("INDEX_REQUIRED — folosește /indexgaze 12345", file=sys.stderr)
        return 1
    index = int(float(sys.argv[1]))
    secrets = load_secrets()
    data = load_data()
    token = ensure_token()
    h = {**headers(token), "Content-Type": "application/json"}
    payload = _payload(index, data)
    r = requests.post(f"{API}/index", headers=h, json=payload, timeout=30)
    if r.status_code == 401:
        refresh_token()
        token = read_token()
        h = {**headers(token), "Content-Type": "application/json"}
        r = requests.post(f"{API}/index", headers=h, json=payload, timeout=30)
    body = r.text[:500]
    if r.status_code == 200:
        _notify(secrets, f"✅ Index gaze Premier trimis\n\n🔢 {index}\n📨 {body}")
        print("OK", index)
        return 0
    _notify(secrets, f"❌ Eroare index gaze\n\n🔢 {index}\nHTTP {r.status_code}\n{body}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
