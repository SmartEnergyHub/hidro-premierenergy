"""Constants for Premier Energy integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "premier_energy"
PLATFORMS: Final = ["sensor", "button", "binary_sensor"]

CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_TELEMETRY_OPT_IN: Final = "telemetry_opt_in"

API_BASE: Final = "https://peremierenergy-portalclient.azurewebsites.net/api"
PORTAL_URL: Final = "https://my.premierenergy.ro"

STORAGE_VERSION: Final = 1
STORAGE_KEY_SESSION: Final = "premier_energy.session"

DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=10)
TOKEN_MARGIN_SECONDS: Final = 1200

ATTR_INVOICE_NUMBER: Final = "invoice_number"
ATTR_DUE_DATE: Final = "due_date"
ATTR_ADDRESS: Final = "address"
ATTR_READING_START: Final = "reading_period_start"
ATTR_READING_STOP: Final = "reading_period_stop"

SERVICE_REFRESH_SESSION: Final = "refresh_session"
SERVICE_FORCE_LOGIN: Final = "force_login"
SERVICE_DOWNLOAD_INVOICE: Final = "download_invoice"
SERVICE_SEND_INDEX: Final = "send_index"
SERVICE_SEND_LAST_INVOICE_TELEGRAM: Final = "send_last_invoice_telegram"
SERVICE_EXPORT_DEBUG: Final = "export_debug"
SERVICE_EXPORT_SUPPORT_BUNDLE: Final = "export_support_bundle"
SERVICE_OPEN_SUPPORT_LINK: Final = "open_support_link"
SERVICE_REPORT_ISSUE: Final = "report_issue"

URL_DONATE: Final = "https://paypal.me/solovip"

REPAIR_AUTH_FAILED: Final = "auth_failed"
