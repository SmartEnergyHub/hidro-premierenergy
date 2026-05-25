"""Transmitere index autocitire iHidro (sync — rulează în executor)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import requests

from .config import API_MAP_FILE, DATA_FILE, PORTAL_BASE, PORTAL_PAGES
from .ha_session import ensure_session
from .logging_util import setup_logger
from .session import requests_session_from_store, validate_session
from .telegram_util import send_telegram

log = setup_logger("hidro.send_index")


def _load_data() -> dict[str, Any]:
    if not DATA_FILE.is_file():
        raise FileNotFoundError("data.json lipsă — apasă Refresh pe integrare")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def validate_index(index: int, data: dict[str, Any]) -> None:
    idx_info = data.get("index") or {}
    if idx_info.get("autocitire_activa") is False:
        log.warning("Autocitire poate fi inactivă — continuăm oricum")
    curent = idx_info.get("curent")
    if curent is not None and index < int(curent):
        raise ValueError(f"Index {index} < index curent portal {curent}")


def _submit_via_http(index: int, data: dict[str, Any], http: requests.Session) -> str:
    payload_candidates = [
        {"MeterReading": str(index), "Reading": str(index), "Index": str(index)},
        {"index": str(index), "meterReading": str(index)},
    ]
    page = PORTAL_PAGES["self_meter"]
    urls = [
        f"{PORTAL_BASE}/{page}",
        f"{PORTAL_BASE}/SelfMeterRead.aspx",
        f"{PORTAL_BASE}/Services/MeterReadingService.svc/SubmitReading",
        f"{PORTAL_BASE}/Handlers/MeterReading.ashx",
    ]
    if API_MAP_FILE.is_file():
        for url in json.loads(API_MAP_FILE.read_text(encoding="utf-8")):
            if re.search(r"meter|index|reading", url, re.I):
                urls.insert(0, url)

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
                    return r.text[:500] or "OK"
            except Exception as exc:
                log.debug("post %s: %s", url, exc)
    raise RuntimeError("Transmitere index eșuată — niciun endpoint HTTP")


def _submit_via_selenium(index: int) -> str:
    import os

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By

    from .common.browser_paths import ensure_browser_deps, resolve_chromedriver, resolve_chromium_bin
    from .common.chromium_lock import ChromiumLock
    from .common.xvfb import ensure_xvfb
    from .config import BROWSER_PROFILE

    ensure_browser_deps(require_xvfb=True)
    display = ensure_xvfb()
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)
    opts = Options()
    opts.binary_location = resolve_chromium_bin()
    for arg in ("--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1920,1080"):
        opts.add_argument(arg)
    opts.add_argument(f"--user-data-dir={BROWSER_PROFILE}")

    with ChromiumLock():
        driver = webdriver.Chrome(
            service=Service(resolve_chromedriver(), env={"DISPLAY": display}),
            options=opts,
        )
        try:
            driver.set_page_load_timeout(120)
            driver.get(f"{PORTAL_BASE}/{PORTAL_PAGES['self_meter']}")
            time.sleep(4)
            if "txtLogin" in driver.page_source:
                raise RuntimeError("Sesiune expirată — apasă Re-login forțat înainte de transmitere index")
            for sel in ("txtReading", "txtIndex", "txtMeterReading", "MeterReading"):
                els = driver.find_elements(By.ID, sel)
                if els:
                    els[0].clear()
                    els[0].send_keys(str(index))
                    break
            else:
                raise RuntimeError("Câmp index negăsit pe pagina autocitire")
            for sel in ("btnSubmit", "btnSave", "Submit", "btnSend"):
                btns = driver.find_elements(By.ID, sel)
                if btns:
                    btns[0].click()
                    break
            time.sleep(8)
            src = driver.page_source.lower()
            if "success" in src or "succes" in src or "inregistr" in src:
                return "OK via browser"
            raise RuntimeError("Transmitere index eșuată via browser")
        finally:
            driver.quit()


def send_index_sync(
    index: int,
    *,
    telegram_bot_token: str = "",
    telegram_chat_id: str = "",
) -> str:
    if index <= 0:
        raise ValueError("Index invalid — completează input_number.hidro_index_curent")

    try:
        if not ensure_session():
            raise RuntimeError("Sesiune invalidă — apasă Re-login forțat")

        data = _load_data()
        validate_index(index, data)
        http = requests_session_from_store()
        if not validate_session(http, touch=False):
            raise RuntimeError("Sesiune invalidă după ensure_session")

        try:
            response_text = _submit_via_http(index, data, http)
        except Exception as http_err:
            log.warning("HTTP index failed: %s — fallback browser", http_err)
            response_text = _submit_via_selenium(index)

        msg = f"✅ Index Hidroelectrica trimis\n\n🔢 Index: {index}\n📨 Răspuns: {response_text[:500]}"
        send_telegram(telegram_bot_token, telegram_chat_id, msg)
        log.info("Index trimis: %s", index)
        return response_text
    except Exception as exc:
        send_telegram(
            telegram_bot_token,
            telegram_chat_id,
            f"❌ Eroare index Hidroelectrica\n\n🔢 Index: {index}\n{exc}",
        )
        raise
