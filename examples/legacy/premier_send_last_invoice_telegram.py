#!/usr/bin/env python3
"""Ultima factură Premier Energy → Telegram (ensure token + PDF base64)."""
from __future__ import annotations

import base64
import sys
from pathlib import Path

import requests

from premier_session import API, BASE, ensure_token, headers, load_secrets


def main() -> int:
    secrets = load_secrets()
    bot = (secrets.get("telegram_bot_token") or "").strip()
    chat = (secrets.get("telegram_chat_id") or "").strip()
    if not bot or not chat or bot == "YOUR_TELEGRAM_BOT_TOKEN":
        print("TELEGRAM_MISSING — completează secrets.json", file=sys.stderr)
        return 1

    token = ensure_token()
    h = headers(token)
    r = requests.get(f"{API}/facturi?Versiunea=1", headers=h, timeout=30)
    if r.status_code == 401:
        from premier_session import refresh_token, read_token

        refresh_token()
        token = read_token()
        h = headers(token)
        r = requests.get(f"{API}/facturi?Versiunea=1", headers=h, timeout=30)
    data = r.json()
    if not isinstance(data, list) or not data:
        print("FACTURI_FAIL", r.status_code, file=sys.stderr)
        return 1

    numar = data[0]["OPBEL"]
    suma = data[0].get("TOTAL_AMNT", "—")
    scadenta = data[0].get("FAEDN", "—")
    rc = requests.get(f"{API}/consum", headers=h, timeout=30)
    m3 = mwh = "—"
    if rc.status_code == 200:
        c = rc.json()
        if c and c[0].get("contracte") and c[0]["contracte"][0].get("consum"):
            row = c[0]["contracte"][0]["consum"][0]
            m3, mwh = row.get("consumM3", "—"), row.get("consumMWH", "—")

    pdf_r = requests.get(f"{API}/facturi/{numar}/pdf", headers=h, timeout=90)
    if pdf_r.status_code != 200:
        print("PDF_FAIL", pdf_r.status_code, file=sys.stderr)
        return 1
    raw = pdf_r.content
    if raw[:4] == b"JVBE":
        raw = base64.b64decode(raw)
    pdf_path = BASE / "facturi" / f"{numar}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(raw)

    msg = (
        f"🔥 FACTURA GAZE PREMIER\n\n💰 {suma} RON\n📅 {scadenta}\n\n"
        f"📊 {m3} m³ / {mwh} MWh\n\n📄 {numar}"
    )
    with pdf_path.open("rb") as pdf:
        tg = requests.post(
            f"https://api.telegram.org/bot{bot}/sendDocument",
            data={"chat_id": chat, "caption": msg[:1024]},
            files={"document": pdf},
            timeout=90,
        )
    if tg.status_code != 200:
        print("TG_FAIL", tg.text[:200], file=sys.stderr)
        return 1
    print("OK", numar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
