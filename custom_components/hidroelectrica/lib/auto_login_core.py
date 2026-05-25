"""Auto-login core — Xvfb + headed Chromium (sync, run in executor)."""

from __future__ import annotations

import os
import shutil
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from .common.chromium_lock import ChromiumLock
from .common.xvfb import ensure_xvfb
from .common.browser_paths import ensure_browser_deps, resolve_chromedriver, resolve_chromium_bin
from .config import (
    BROWSER_PROFILE,
    MAX_RETRIES,
    PORTAL_LOGIN,
    RECAPTCHA_SITE_KEY,
)
from .logging_util import setup_logger
from .session import (
    cookies_from_selenium,
    extract_csrf_from_html,
    load_secrets,
    requests_session_from_store,
    save_session,
    validate_session,
)

log = setup_logger("hidro.auto_login")

_CHROME_STABILITY_ARGS = (
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--no-zygote",
    "--disable-software-rasterizer",
    "--window-size=1920,1080",
    "--disable-blink-features=AutomationControlled",
)


def _reset_browser_profile() -> None:
    if not BROWSER_PROFILE.is_dir():
        return
    backup = BROWSER_PROFILE.with_name(f"{BROWSER_PROFILE.name}_broken_{int(time.time())}")
    try:
        BROWSER_PROFILE.rename(backup)
        log.warning("Profil browser resetat (vechi: %s)", backup.name)
    except OSError as exc:
        log.warning("Nu am putut reseta profilul browser: %s", exc)
        shutil.rmtree(BROWSER_PROFILE, ignore_errors=True)


def _login_with_browser(username: str, password: str) -> bool:
    ensure_browser_deps(require_xvfb=True)
    display = ensure_xvfb()
    chromium = resolve_chromium_bin()
    chromedriver = resolve_chromedriver()
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)

    opts = Options()
    opts.binary_location = chromium
    for arg in _CHROME_STABILITY_ARGS:
        opts.add_argument(arg)
    opts.add_argument(f"--user-data-dir={BROWSER_PROFILE}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(
        service=Service(chromedriver, env={"DISPLAY": display}),
        options=opts,
    )
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'},
    )
    try:
        driver.set_page_load_timeout(120)
        driver.get(PORTAL_LOGIN)
        time.sleep(6)
        if "txtLogin" not in driver.page_source:
            log.info("Browser profile already authenticated")
        else:
            token = None
            try:
                driver.set_script_timeout(45)
                token = driver.execute_async_script(
                    """
                    const cb = arguments[arguments.length - 1];
                    const key = arguments[0];
                    function run() {
                        if (typeof grecaptcha === 'undefined') { cb(''); return; }
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
            if token:
                driver.execute_script(
                    "document.querySelectorAll('[name=g-recaptcha-response]').forEach(e => e.value = arguments[0])",
                    token,
                )
            driver.find_element(By.ID, "txtLogin").clear()
            driver.find_element(By.ID, "txtLogin").send_keys(username)
            driver.find_element(By.ID, "txtpwd").clear()
            driver.find_element(By.ID, "txtpwd").send_keys(password)
            driver.execute_script("document.getElementById('btnlogin').click()")
            for _ in range(45):
                time.sleep(1)
                if "invalid captcha" in driver.page_source.lower():
                    raise RuntimeError("Invalid Captcha")
                if "txtLogin" not in driver.page_source:
                    break
            else:
                raise RuntimeError("Login timeout")

        csrf = extract_csrf_from_html(driver.page_source)
        cookies = cookies_from_selenium(driver)
        save_session(
            cookies,
            csrf=csrf,
            extra={
                "login_method": "auto_xvfb",
                "source": "auto_login",
                "last_auto_login": time.time(),
            },
        )
        return True
    finally:
        driver.quit()


def auto_login_sync() -> bool:
    secrets = load_secrets()
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with ChromiumLock():
                _login_with_browser(secrets["username"], secrets["password"])
            if validate_session(requests_session_from_store()):
                return True
            raise RuntimeError("Session invalid after login")
        except Exception as exc:
            last_err = exc
            log.error("Auto-login attempt %d: %s", attempt, exc)
            if "unable to connect to renderer" in str(exc).lower() and attempt < MAX_RETRIES:
                _reset_browser_profile()
            if attempt < MAX_RETRIES:
                time.sleep(5 * attempt)
    log.error("Auto-login failed: %s", last_err)
    return False
