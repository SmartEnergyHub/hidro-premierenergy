"""DataUpdateCoordinator for Premier Energy."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_EMAIL, CONF_PASSWORD, DEFAULT_SCAN_INTERVAL, DOMAIN
from .lib.api_client import PremierApiClient
from .lib.auth_manager import PremierAuthManager
from .lib.storage import PremierStorage

_LOGGER = logging.getLogger(__name__)


class PremierCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch Premier Energy data with auto token refresh."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.storage = PremierStorage(hass, entry.entry_id)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self._auth = PremierAuthManager(
            email=entry.data[CONF_EMAIL],
            password=entry.data[CONF_PASSWORD],
            storage_dir=self.storage.base_dir,
            browser_profile=self.storage.browser_profile,
            debug_dir=self.storage.debug_dir,
        )
        self.last_auth_method = "unknown"
        self.auth_ok = False

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            token = await self.hass.async_add_executor_job(self._auth.refresh_token)
            await self.hass.async_add_executor_job(self.storage.write_token_sync, token)
            self.auth_ok = True
            self.last_auth_method = "cache" if self._auth.token_is_valid(token) else "browser"
            data = await self.hass.async_add_executor_job(PremierApiClient(token).fetch_all)
            data["token_margin_sec"] = self._token_margin(token)
            data["health_status"] = "ok"
            data["updated_at"] = time.time()
            await self.storage.async_save(
                {
                    "token_exp": self._auth.decode_jwt_payload(token or "") or {},
                    "last_update": data["updated_at"],
                    "health_status": "ok",
                }
            )
            self.storage.write_health_sync(
                {
                    "status": "ok",
                    "service": DOMAIN,
                    "token_margin_sec": data.get("token_margin_sec"),
                    "updated_at": data["updated_at"],
                }
            )
            return data
        except Exception as err:
            self.auth_ok = False
            self.storage.write_health_sync(
                {"status": "failed", "service": DOMAIN, "reason": str(err)}
            )
            raise UpdateFailed(f"Premier Energy update failed: {err}") from err

    async def async_force_login(self) -> None:
        token = await self.hass.async_add_executor_job(lambda: self._auth.refresh_token(force=True))
        await self.hass.async_add_executor_job(self.storage.write_token_sync, token)
        await self.async_request_refresh()

    async def async_refresh_session(self) -> None:
        await self.async_request_refresh()

    def _token_margin(self, token: str) -> int | None:
        payload = self._auth.decode_jwt_payload(token)
        if payload and payload.get("exp"):
            return int(payload["exp"] - time.time())
        return None

    async def async_download_invoice(self, invoice_number: str) -> str | None:
        token = await self.hass.async_add_executor_job(self._auth.read_token)
        if not token:
            token = await self.hass.async_add_executor_job(self._auth.refresh_token)
        return await self.hass.async_add_executor_job(
            lambda: PremierApiClient(token).download_invoice_pdf(
                invoice_number, self.storage.invoices_dir
            )
        )

    async def async_send_index(self, index: int) -> str:
        token = await self.hass.async_add_executor_job(self._auth.refresh_token)
        result = await self.hass.async_add_executor_job(lambda: self._send_index_sync(index, token))
        await self.async_request_refresh()
        return result

    async def async_send_last_invoice_telegram(self) -> str:
        from pathlib import Path

        from .lib.send_last_invoice_core import send_last_invoice_telegram_sync

        secrets_dir = Path(self.hass.config.config_dir) / DOMAIN
        return await self.hass.async_add_executor_job(
            lambda: send_last_invoice_telegram_sync(
                self._auth,
                self.storage.invoices_dir,
                coordinator_data=self.data,
                secrets_dir=secrets_dir,
            )
        )

    def _send_index_sync(self, index: int, token: str) -> str:
        from .lib.send_index_core import send_index_sync

        secrets_dir = Path(self.hass.config.config_dir) / DOMAIN
        return send_index_sync(
            index,
            token,
            self.data,
            secrets_dir=secrets_dir,
        )

    def export_debug(self) -> dict[str, Any]:
        token = self._auth.read_token()
        margin = self._token_margin(token) if token else None
        return {
            "entry_id": self.entry.entry_id,
            "auth_ok": self.auth_ok,
            "last_auth_method": self.last_auth_method,
            "storage_dir": str(self.storage.base_dir),
            "health_file": str(self.storage.base_dir / "health.json"),
            "token_margin_sec": margin,
            "coordinator_last_success": self.last_update_success,
        }

    async def async_export_support_bundle(self) -> str:
        from .lib.support import build_support_bundle

        log_path = Path(self.hass.config.config_dir) / "home-assistant.log"
        log_excerpt = ""
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
                "title": "Premier Energy — Support",
                "message": f"[Deschide link-ul]({url})",
                "notification_id": f"{DOMAIN}_support_{link_key}",
            },
        )
        return url
