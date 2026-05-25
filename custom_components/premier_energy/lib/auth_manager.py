"""Premier Energy auth — Azure B2C auto-login (Selenium + persistent profile)."""

from __future__ import annotations

import base64
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .common.browser_paths import ensure_browser_deps, resolve_chromedriver, resolve_chromium_bin
from .common.chromium_lock import ChromiumLock

_LOGGER = logging.getLogger(__name__)

API_BASE = "https://peremierenergy-portalclient.azurewebsites.net/api"
PORTAL_URL = "https://my.premierenergy.ro"
MAX_ATTEMPTS = 3
LOGIN_WAIT_SECONDS = 90
TOKEN_MARGIN_SECONDS = 1200
JWT_RE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
LOGIN_URL_HINTS = ("login.premierenergy.ro", "oauth2", "authorize", "signup_signin")


class PremierAuthManager:
    """Sync auth manager — run via executor from HA coordinator."""

    def __init__(
        self,
        email: str,
        password: str,
        storage_dir: Path,
        browser_profile: Path,
        debug_dir: Path,
    ) -> None:
        self.email = email
        self.password = password
        self.storage_dir = storage_dir
        self.browser_profile = browser_profile
        self.debug_dir = debug_dir
        self.token_file = storage_dir / "token.txt"

    def decode_jwt_payload(self, token: str) -> dict[str, Any] | None:
        if not JWT_RE.match(token):
            return None
        try:
            part = token.split(".")[1]
            pad = "=" * (-len(part) % 4)
            return json.loads(base64.urlsafe_b64decode(part + pad).decode("utf-8"))
        except Exception:
            return None

    def token_is_valid(self, token: str, margin: int = TOKEN_MARGIN_SECONDS) -> bool:
        payload = self.decode_jwt_payload(token)
        if not payload:
            return False
        exp = payload.get("exp")
        return isinstance(exp, (int, float)) and (exp - time.time()) > margin

    def validate_token_via_api(self, token: str) -> bool:
        try:
            r = requests.get(
                f"{API_BASE}/locConsum?cuAdresa=true",
                headers={"Premier-Auth": f"Bearer {token}", "Accept": "application/json"},
                timeout=25,
            )
            return r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0
        except Exception as exc:
            _LOGGER.debug("API probe: %s", exc)
            return False

    def read_token(self) -> str | None:
        if not self.token_file.is_file():
            return None
        t = self.token_file.read_text(encoding="utf-8").strip()
        return t or None

    def save_token(self, token: str) -> None:
        self.token_file.write_text(token, encoding="utf-8")

    def _token_margin_sec(self, token: str) -> int | None:
        payload = self.decode_jwt_payload(token)
        if payload and payload.get("exp"):
            return int(payload["exp"] - time.time())
        return None

    def _create_driver(self) -> webdriver.Chrome:
        ensure_browser_deps()
        chromium = resolve_chromium_bin()
        chromedriver = resolve_chromedriver()
        self.browser_profile.mkdir(parents=True, exist_ok=True)
        opts = Options()
        opts.binary_location = chromium
        opts.add_argument(f"--user-data-dir={self.browser_profile}")
        for arg in (
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1280,900",
            "--disable-blink-features=AutomationControlled",
        ):
            opts.add_argument(arg)
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Chrome(service=Service(chromedriver), options=opts)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'},
        )
        driver.set_page_load_timeout(120)
        return driver

    @staticmethod
    def _is_login_url(url: str) -> bool:
        u = url.lower()
        return any(h in u for h in LOGIN_URL_HINTS)

    def _extract_token(self, driver: webdriver.Chrome) -> str | None:
        script = """
        const keys = ['id_token','idToken','token'];
        for (const k of keys) {
            const v = localStorage.getItem(k);
            if (v && v.split('.').length === 3) return v;
        }
        const hash = window.location.hash || '';
        if (hash.includes('id_token=')) {
            const p = new URLSearchParams(hash.replace(/^#/, ''));
            return p.get('id_token');
        }
        return null;
        """
        try:
            token = driver.execute_script(script)
            if token and JWT_RE.match(token):
                return token
        except Exception as exc:
            _LOGGER.debug("extract_token: %s", exc)
        return None

    def _perform_login(self, driver: webdriver.Chrome) -> None:
        wait = WebDriverWait(driver, 60)
        email_el = None
        for selector in ("signInName", "logonIdentifier"):
            try:
                wait.until(EC.presence_of_element_located((By.ID, selector)))
                email_el = driver.find_element(By.ID, selector)
                break
            except Exception:
                continue
        if not email_el:
            raise RuntimeError("Login form not found")
        driver.find_element(By.ID, "password").clear()
        email_el.clear()
        email_el.send_keys(self.email)
        driver.find_element(By.ID, "password").send_keys(self.password)
        driver.find_element(By.ID, "next").click()
        deadline = time.time() + LOGIN_WAIT_SECONDS
        while time.time() < deadline:
            src = driver.page_source.lower()
            if any(
                hint in src
                for hint in (
                    "password is incorrect",
                    "parola este incorect",
                    "parola introdus",
                    "invalid username or password",
                    "contul de utilizator nu exist",
                )
            ):
                raise RuntimeError("Invalid email or password")
            token = self._extract_token(driver)
            if token and self.token_is_valid(token, margin=60):
                return
            if "my.premierenergy.ro" in driver.current_url and not self._is_login_url(
                driver.current_url
            ):
                if self._extract_token(driver):
                    return
            time.sleep(1)
        raise RuntimeError("Login timeout — token not found")

    def refresh_token(self, *, force: bool = False) -> str:
        cached = self.read_token()
        if cached and not force:
            margin = self._token_margin_sec(cached)
            if (
                margin is not None
                and margin > TOKEN_MARGIN_SECONDS
                and self.validate_token_via_api(cached)
            ):
                return cached
            if margin is not None and margin <= TOKEN_MARGIN_SECONDS:
                _LOGGER.info(
                    "Token expiră în %ds — refresh proactiv (prag %ds)",
                    margin,
                    TOKEN_MARGIN_SECONDS,
                )
                force = True

        last_err: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                with ChromiumLock():
                    driver = self._create_driver()
                    try:
                        driver.get(PORTAL_URL)
                        time.sleep(2)
                        token = self._extract_token(driver)
                        if token and self.token_is_valid(token, margin=60):
                            self.save_token(token)
                            return token
                        if self._is_login_url(driver.current_url) or driver.find_elements(
                            By.ID, "signInName"
                        ):
                            self._perform_login(driver)
                        token = self._extract_token(driver)
                        if not token:
                            dump = self.debug_dir / f"fail_{int(time.time())}.html"
                            dump.write_text(driver.page_source, encoding="utf-8")
                            raise RuntimeError("id_token not found after login")
                        self.save_token(token)
                        return token
                    finally:
                        driver.quit()
            except Exception as exc:
                last_err = exc
                _LOGGER.warning("Auth attempt %d failed: %s", attempt, exc)
                if attempt < MAX_ATTEMPTS:
                    time.sleep(5 * attempt)
        raise RuntimeError(f"Premier auth failed: {last_err}")
