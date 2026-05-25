#!/usr/bin/env python3
"""Transmitere index autocitire Hidroelectrica + Telegram."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.config import DATA_FILE, PORTAL_BASE
from lib.logging_util import setup_logger
from lib.session import load_secrets, validate_session, requests_session_from_store
from lib.telegram_util import send_telegram

log = setup_logger("hidro.send_index")

RESTORE_STATE = Path("/config/.storage/core.restore_state")
INPUT_ENTITY = "input_number.hidro_index_curent"


def read_index_from_ha() -> Optional[str]:
    if not RESTORE_STATE.is_file():
        return None
    try:
        store = json.loads(RESTORE_STATE.read_text(encoding="utf-8"))
        for item in store.get("data", []):
            if item.get("state", {}).get("entity_id") == INPUT_ENTITY:
                return item["state"]["state"]
    except Exception as exc:
        log.debug("restore_state: %s", exc)
    return None


def validate_index(index: int, data: dict) -> None:
    idx_info = data.get("index") or {}
    if idx_info.get("autocitire_activa") is False:
        log.warning("Autocitire poate fi inactivă — continuăm oricum")
    curent = idx_info.get("curent")
    if curent is not None and index < int(curent):
        raise ValueError(f"Index {index} < index curent portal {curent}")


def submit_index_http(index: int, data: dict, http: requests.Session) -> requests.Response:
    """POST către endpoint-uri comune SEW / autocitire."""
    payload_candidates = [
        {"MeterReading": str(index), "Reading": str(index), "Index": str(index)},
        {"index": str(index), "meterReading": str(index)},
    ]
    urls = [
        f"{PORTAL_BASE}/SelfMeterRead.aspx",
        f"{PORTAL_BASE}/Services/MeterReadingService.svc/SubmitReading",
        f"{PORTAL_BASE}/Handlers/MeterReading.ashx",
    ]
    api_map = Path(__file__).resolve().parent / "api_endpoints.json"
    if api_map.is_file():
        for u in json.loads(api_map.read_text(encoding="utf-8")):
            if re.search(r"meter|index|reading", u, re.I):
                urls.insert(0, u)

    contract = data.get("contract") or ""
    pod = data.get("pod") or ""
    for url in urls:
        for payload in payload_candidates:
            body = {**payload, "AccountNumber": contract, "POD": pod}
            try:
                if url.endswith(".aspx"):
                    r = http.post(url, data=body, timeout=45)
                else:
                    r = http.post(url, json=body, timeout=45)
                log.debug("POST %s -> %s %s", url[:80], r.status_code, r.text[:120])
                if r.status_code in (200, 201, 204) and "error" not in r.text.lower()[:200]:
                    return r
            except Exception as exc:
                log.debug("post %s: %s", url, exc)

    # Fallback Selenium
    from lib.browser_auth import selenium_login

    from selenium.webdriver.common.by import By

    secrets = load_secrets()
    driver = selenium_login(secrets["username"], secrets["password"])
    try:
        driver.get(f"{PORTAL_BASE}/SelfMeterRead.aspx")
        time.sleep(4)
        for sel in ("txtReading", "txtIndex", "txtMeterReading", "MeterReading"):
            els = driver.find_elements(By.ID, sel)
            if els:
                els[0].clear()
                els[0].send_keys(str(index))
                break
        for sel in ("btnSubmit", "btnSave", "Submit"):
            btns = driver.find_elements(By.ID, sel)
            if btns:
                btns[0].click()
                break
        time.sleep(8)
        src = driver.page_source.lower()
        if "success" in src or "succes" in src or "inregistr" in src:
            class R:
                status_code = 200
                text = "OK via Selenium"
            return R()
        raise RuntimeError("Transmitere index eșuată via browser")
    finally:
        driver.quit()


def main() -> int:
    secrets = load_secrets()
    index_raw = read_index_from_ha() or secrets.get("default_index", "")
    if not index_raw:
        log.error("Index negăsit în %s", INPUT_ENTITY)
        return 1
    index = int(float(index_raw))

    if not DATA_FILE.is_file():
        log.error("data.json lipsă")
        return 1
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    validate_index(index, data)

    if not validate_session(requests_session_from_store()):
        from refresh_session import main as refresh_main
        if refresh_main() != 0:
            return 1

    http = requests_session_from_store()
    try:
        resp = submit_index_http(index, data, http)
        msg = f"✅ Index Hidroelectrica trimis\n\n🔢 Index: {index}\n📨 Răspuns: {resp.text[:500]}"
        send_telegram(secrets.get("telegram_bot_token", ""), secrets.get("telegram_chat_id", ""), msg)
        log.info("Index trimis: %s", index)
        return 0
    except Exception as exc:
        msg = f"❌ Eroare index Hidroelectrica\n\n🔢 Index: {index}\n{exc}"
        send_telegram(secrets.get("telegram_bot_token", ""), secrets.get("telegram_chat_id", ""), msg)
        log.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
