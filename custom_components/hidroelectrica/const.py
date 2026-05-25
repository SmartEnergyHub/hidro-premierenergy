"""Constants for Hidroelectrica integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "hidroelectrica"
PLATFORMS: Final = ["sensor", "button", "binary_sensor"]

CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_TELEGRAM_BOT_TOKEN: Final = "telegram_bot_token"
CONF_TELEGRAM_CHAT_ID: Final = "telegram_chat_id"
CONF_TELEMETRY_OPT_IN: Final = "telemetry_opt_in"

DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=5)

SERVICE_REFRESH_SESSION: Final = "refresh_session"
SERVICE_FORCE_LOGIN: Final = "force_login"
SERVICE_DOWNLOAD_INVOICE: Final = "download_invoice"
SERVICE_SEND_INDEX: Final = "send_index"
SERVICE_SEND_LAST_INVOICE_TELEGRAM: Final = "send_last_invoice_telegram"
SERVICE_EXPORT_DEBUG: Final = "export_debug"
SERVICE_EXPORT_SUPPORT_BUNDLE: Final = "export_support_bundle"
SERVICE_OPEN_SUPPORT_LINK: Final = "open_support_link"
SERVICE_REPORT_ISSUE: Final = "report_issue"

STORAGE_VERSION: Final = 1
STORAGE_KEY_SESSION: Final = "hidroelectrica.session"

REPAIR_AUTH_FAILED: Final = "auth_failed"

URL_DONATE: Final = "https://paypal.me/solovip"
