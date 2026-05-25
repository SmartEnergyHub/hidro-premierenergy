#!/usr/bin/env python3
"""Refresh JWT Premier Energy — rulează pe HOST (Chromium + Selenium)."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

BASE = Path("/config/premier_energy")
SECRETS = BASE / "secrets.json"
PORTAL_URL = "https://my.premierenergy.ro"
API_BASE = "https://peremierenergy-portalclient.azurewebsites.net/api"
JWT_RE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
LOGIN_HINTS = ("login.premierenergy.ro", "oauth2", "authorize", "signup_signin")


def _token_file() -> Path:
    for d in [BASE, *BASE.iterdir() if BASE.is_dir() else []]:
        if d.is_dir() and (d / "token.txt").is_file():
            return d / "token.txt"
    return BASE / "token.txt"


def _load_creds() -> tuple[str, str]:
    if not SECRETS.is_file():
        print("SECRETS_MISSING — copiază premier_secrets.json.example → secrets.json", file=sys.stderr)
        sys.exit(1)
    data = json.loads(SECRETS.read_text(encoding="utf-8"))
    email = (data.get("email") or data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    if not email or not password or password == "your_password_here":
        print("INVALID_SECRETS — completează email și password în secrets.json", file=sys.stderr)
        sys.exit(1)
    return email, password


def _chromium() -> tuple[str, str]:
    import os
    import shutil

    for name in ("chromium", "chromium-browser", "google-chrome"):
        p = shutil.which(name)
        if p:
            break
    else:
        print("CHROMIUM_MISSING", file=sys.stderr)
        sys.exit(1)
    driver = shutil.which("chromedriver") or "/usr/bin/chromedriver"
    return p, driver


def _extract_token(driver: webdriver.Chrome) -> str | None:
    script = """
    const keys = ['id_token','idToken','token'];
    for (const k of keys) {
      const v = localStorage.getItem(k) || sessionStorage.getItem(k);
      if (v) return v;
    }
    if (location.hash.includes('id_token=')) {
      return new URLSearchParams(location.hash.slice(1)).get('id_token');
    }
    return null;
    """
    token = driver.execute_script(script)
    if token and JWT_RE.match(token):
        return token
    return None


def _is_login(url: str) -> bool:
    u = url.lower()
    return any(h in u for h in LOGIN_HINTS)


def _login(driver: webdriver.Chrome, email: str, password: str) -> str:
    driver.get(PORTAL_URL)
    time.sleep(2)
    token = _extract_token(driver)
    if token:
        return token
    if _is_login(driver.current_url) or driver.find_elements(By.ID, "signInName"):
        driver.find_element(By.ID, "signInName").clear()
        driver.find_element(By.ID, "signInName").send_keys(email)
        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "next").click()
        deadline = time.time() + 90
        while time.time() < deadline:
            token = _extract_token(driver)
            if token:
                return token
            if "password is incorrect" in driver.page_source.lower():
                raise RuntimeError("Invalid email or password")
            time.sleep(1)
    raise RuntimeError("Login timeout — token not found")


def main() -> int:
    email, password = _load_creds()
    chromium, chromedriver = _chromium()
    profile = BASE / "browser_profile"
    profile.mkdir(parents=True, exist_ok=True)
    opts = Options()
    opts.binary_location = chromium
    opts.add_argument(f"--user-data-dir={profile}")
    for arg in ("--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1280,900"):
        opts.add_argument(arg)
    driver = webdriver.Chrome(service=Service(chromedriver), options=opts)
    try:
        token = _login(driver, email, password)
        out = _token_file()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(token, encoding="utf-8")
        print("TOKEN_OK")
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
