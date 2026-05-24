"""Autentificare browser Selenium + interceptare rețea."""

from __future__ import annotations

import json
import re
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from .config import (
    API_MAP_FILE,
    CHROMEDRIVER,
    CHROMIUM_BIN,
    PORTAL_LOGIN,
    RECAPTCHA_SITE_KEY,
)
from .logging_util import setup_logger
from .session import cookies_from_selenium, extract_csrf_from_html, save_session

log = setup_logger("hidro.browser")


def _chrome_options(headless: bool = True) -> Options:
    opts = Options()
    opts.binary_location = CHROMIUM_BIN
    if headless:
        opts.add_argument("--headless=new")
    for arg in (
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--disable-blink-features=AutomationControlled",
    ):
        opts.add_argument(arg)
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return opts


def _recaptcha_token(driver, timeout: int = 45) -> str | None:
    driver.set_script_timeout(timeout)
    try:
        return driver.execute_async_script(
            """
            const cb = arguments[arguments.length - 1];
            const key = arguments[0];
            function run() {
                if (typeof grecaptcha === 'undefined') {
                    cb('');
                    return;
                }
                grecaptcha.ready(function() {
                    grecaptcha.execute(key, {action: 'login'})
                        .then(function(t) { cb(t || ''); })
                        .catch(function() { cb(''); });
                });
            }
            run();
            """,
            RECAPTCHA_SITE_KEY,
        )
    except TimeoutException:
        log.warning("reCAPTCHA timeout")
        return None


def _collect_perf_urls(driver) -> set[str]:
    urls: set[str] = set()
    try:
        entries = driver.get_log("performance")
        for entry in entries:
            msg = json.loads(entry["message"])["message"]
            if msg.get("method") != "Network.responseReceived":
                continue
            url = msg.get("params", {}).get("response", {}).get("url", "")
            if url and "ihidro.ro" in url:
                urls.add(url)
    except Exception as exc:
        log.debug("perf log: %s", exc)
    return urls


def _save_api_map(urls: set[str]) -> None:
    interesting = sorted(
        u
        for u in urls
        if re.search(
            r"api|service|ashx|asmx|bill|invoice|usage|meter|consum|index|account|dashboard",
            u,
            re.I,
        )
    )
    if not interesting:
        return
    existing: list[str] = []
    if API_MAP_FILE.is_file():
        try:
            existing = json.loads(API_MAP_FILE.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    merged = sorted(set(existing) | set(interesting))
    API_MAP_FILE.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    log.info("API map updated (%d URLs)", len(merged))


def selenium_login(username: str, password: str, headless: bool = True) -> webdriver.Chrome:
    log.info("Selenium login (headless=%s)", headless)
    driver = webdriver.Chrome(
        service=Service(CHROMEDRIVER),
        options=_chrome_options(headless=headless),
    )
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'},
    )
    driver.set_page_load_timeout(120)

    driver.get(PORTAL_LOGIN)
    time.sleep(6)

    token = _recaptcha_token(driver)
    if token:
        driver.execute_script(
            "document.querySelectorAll('[name=g-recaptcha-response]').forEach(e => e.value = arguments[0])",
            token,
        )
        log.debug("reCAPTCHA token len=%d", len(token))
    else:
        log.warning("No reCAPTCHA token — login may fail")

    driver.find_element(By.ID, "txtLogin").clear()
    driver.find_element(By.ID, "txtLogin").send_keys(username)
    driver.find_element(By.ID, "txtpwd").clear()
    driver.find_element(By.ID, "txtpwd").send_keys(password)
    driver.execute_script("document.getElementById('btnlogin').click()")

    for _ in range(30):
        time.sleep(1)
        src = driver.page_source.lower()
        if "invalid captcha" in src:
            raise RuntimeError(
                "Login eșuat: Invalid Captcha (headless blocat — folosește import_session.py)"
            )
        if "incorect" in src or "incorrect" in src:
            if "txtlogin" in src and "btnlogin" in src:
                raise RuntimeError("Login eșuat: credențiale incorecte")
        if "txtlogin" not in src or driver.current_url.lower() not in (
            PORTAL_LOGIN.lower(),
            PORTAL_LOGIN.lower().rstrip("/"),
        ):
            break
    else:
        raise RuntimeError("Login timeout")

    urls = _collect_perf_urls(driver)
    _save_api_map(urls)

    csrf = extract_csrf_from_html(driver.page_source)
    cookies = cookies_from_selenium(driver)
    save_session(
        cookies, csrf=csrf, extra={"login_method": "selenium", "login_url": driver.current_url}
    )
    log.info("Login OK url=%s cookies=%d", driver.current_url[:80], len(cookies))
    return driver


def browse_logged_in_pages(driver: webdriver.Chrome) -> dict[str, str]:
    from .config import DASHBOARD_PATHS, PORTAL_BASE

    pages: dict[str, str] = {}
    for page in DASHBOARD_PATHS:
        url = f"{PORTAL_BASE}/{page}"
        try:
            driver.get(url)
            time.sleep(3)
            pages[page] = driver.page_source
            _save_api_map(_collect_perf_urls(driver))
        except Exception as exc:
            log.warning("page %s: %s", page, exc)
    return pages
