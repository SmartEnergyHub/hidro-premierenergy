"""Căi și constante Hidroelectrica iHidro."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_base_dir() -> Path:
    override = os.environ.get("HIDROELECTRICA_DIR")
    if override:
        return Path(override)
    for path in (
        Path("/config/hidroelectrica"),
        Path("/homeassistant/hidroelectrica"),
        Path("/opt/hidroelectrica"),
    ):
        if path.is_dir():
            return path
    return Path("/config/hidroelectrica")


BASE_DIR = resolve_base_dir()
BACKUPS_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"
INVOICES_DIR = BASE_DIR / "invoices"
LIB_DIR = BASE_DIR / "lib"
BROWSER_PROFILE = BASE_DIR / "browser_profile"
HEALTH_FILE = BASE_DIR / "health.json"

SECRETS_FILE = BASE_DIR / "secrets.json"
SESSION_FILE = BASE_DIR / "session.json"
COOKIES_IMPORT_FILE = BASE_DIR / "cookies_import.json"
DATA_FILE = BASE_DIR / "data.json"
TOKEN_FILE = BASE_DIR / "token.txt"
API_MAP_FILE = BASE_DIR / "api_endpoints.json"
LAST_INVOICE_FILE = BASE_DIR / "last_invoice.txt"
CHANGELOG_FILE = BASE_DIR / "backups" / "changelog.log"

PORTAL_BASE = "https://ihidro.ro/portal"
PORTAL_LOGIN = f"{PORTAL_BASE}/"
RECAPTCHA_SITE_KEY = "6LdWVgYfAAAAAOtv1JCMvOVYagKN_I7Tt8EMCBWx"

CHROMIUM_BIN = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")
CHROMEDRIVER = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

MAX_RETRIES = 3
SESSION_MARGIN_HOURS = 12


PORTAL_PAGES = {
    "billing": "BillingHistory.aspx",
    "index_history": "IndexHistory.aspx",
    "self_meter": "SelfMeterReading.aspx",
    "usages": "usages.aspx",
    "convention": "ConsumerAgreement.aspx",
    "dashboard": "Dashboard.aspx",
}

DASHBOARD_PATHS = tuple(PORTAL_PAGES.values())

API_ENDPOINTS = {
    "pods": "IndexHistory.aspx/GetAllPODBind",
    "index_grid": "IndexHistory.aspx/LoadW2UIGridData",
    "billing_grid": "BillingHistory.aspx/LoadW2UIGridData",
}
