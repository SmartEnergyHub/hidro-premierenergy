"""DataUpdateCoordinator for Hidroelectrica."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_PASSWORD,
    CONF_TELEGRAM_BOT_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .lib.api_client import download_invoice_pdf, fetch_all_data
from .lib.ha_session import ensure_session, setup_storage_dir
from .lib.secrets_sync import write_secrets_sync
from .lib.storage import HidroStorage

_LOGGER = logging.getLogger(__name__)


class HidroCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.storage = HidroStorage(hass, entry.entry_id)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.session_ok = False

    def _prepare_sync_env(self) -> None:
        setup_storage_dir(self.storage.base_dir)
        write_secrets_sync(
            self.storage.base_dir,
            username=self.entry.data[CONF_USERNAME],
            password=self.entry.data[CONF_PASSWORD],
            telegram_bot_token=self.entry.data.get(CONF_TELEGRAM_BOT_TOKEN, ""),
            telegram_chat_id=self.entry.data.get(CONF_TELEGRAM_CHAT_ID, ""),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            await self.hass.async_add_executor_job(self._prepare_sync_env)
            ok = await self.hass.async_add_executor_job(ensure_session)
            self.session_ok = ok
            if not ok:
                raise RuntimeError("Session recovery failed")

            data = await self.hass.async_add_executor_job(fetch_all_data)
            data["health_status"] = "ok"
            data["session_valid"] = True
            data["updated_at"] = time.time()
            await self.storage.async_save(
                {"last_update": data["updated_at"], "health_status": "ok"}
            )
            self.storage.write_health_sync(
                {"status": "ok", "service": DOMAIN, "updated_at": data["updated_at"]}
            )
            return data
        except Exception as err:
            self.session_ok = False
            self.storage.write_health_sync(
                {"status": "failed", "service": DOMAIN, "reason": str(err)}
            )
            raise UpdateFailed(f"Hidroelectrica update failed: {err}") from err

    async def async_force_login(self) -> None:
        from .lib.auto_login_core import auto_login_sync

        await self.hass.async_add_executor_job(self._prepare_sync_env)
        await self.hass.async_add_executor_job(auto_login_sync)
        await self.async_request_refresh()

    async def async_download_invoice(self, invoice_number: str) -> str | None:
        await self.hass.async_add_executor_job(self._prepare_sync_env)
        await self.hass.async_add_executor_job(ensure_session)
        return await self.hass.async_add_executor_job(lambda: download_invoice_pdf(invoice_number))

    def export_debug(self) -> dict[str, Any]:
        from .lib.config import HEALTH_FILE, SESSION_FILE
        from .lib.session import load_session

        session = load_session() or {}
        return {
            "entry_id": self.entry.entry_id,
            "session_ok": self.session_ok,
            "storage_dir": str(self.storage.base_dir),
            "session_file": str(SESSION_FILE),
            "session_cookies_count": len(session.get("cookies", [])),
            "session_has_csrf": bool(session.get("csrf")),
            "health_file": str(HEALTH_FILE),
            "last_update": (self.data or {}).get("updated_at"),
            "coordinator_last_success": self.last_update_success,
        }

    async def async_export_support_bundle(self) -> str:
        from .lib.support import build_support_bundle

        log_excerpt = ""
        log_path = self.storage.base_dir / "logs" / "hidro.session.log"
        if log_path.is_file():
            log_excerpt = log_path.read_text(encoding="utf-8", errors="replace")[-30000:]

        path = await self.hass.async_add_executor_job(
            build_support_bundle,
            Path(self.hass.config.config_dir),
            DOMAIN,
            self.entry.entry_id,
            self.export_debug(),
            log_excerpt,
        )
        return str(path)

    async def async_notify_support_link(self, link_key: str) -> str:
        from .lib.support import SUPPORT_LINKS

        url = SUPPORT_LINKS.get(link_key, SUPPORT_LINKS["support"])
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Hidroelectrica — Support",
                "message": f"[Deschide link-ul]({url})",
                "notification_id": f"{DOMAIN}_support_{link_key}",
            },
        )
        return url
