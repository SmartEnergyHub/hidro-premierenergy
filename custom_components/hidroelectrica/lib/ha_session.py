"""HA-adapted session manager for Hidroelectrica (uses HIDROELECTRICA_DIR env)."""

from __future__ import annotations

import os
import time
from pathlib import Path

from .logging_util import setup_logger
from .session import (
    cookies_import_is_fresher,
    requests_session_from_store,
    try_recover_session,
    validate_session,
)

log = setup_logger("hidro.session_mgr")


def _validate_with_retries(tries: int = 3, delay: float = 2.0) -> bool:
    for attempt in range(1, tries + 1):
        if validate_session(requests_session_from_store()):
            return True
        if attempt < tries:
            time.sleep(delay)
    return False


def ensure_session(*, allow_auto_login: bool = True) -> bool:
    if _validate_with_retries():
        return True

    log.warning("Sesiune invalidă — recovery automat (auto-login)")

    if allow_auto_login:
        from .auto_login_core import auto_login_sync

        if auto_login_sync() and _validate_with_retries(tries=2, delay=1.0):
            return True

    if cookies_import_is_fresher() and try_recover_session():
        if _validate_with_retries(tries=2, delay=1.0):
            return True

    # Ultimă șansă: cookies_import chiar dacă e mai vechi decât session.json corupt
    if try_recover_session(force=True):
        if _validate_with_retries(tries=2, delay=1.0):
            return True

    return False


def setup_storage_dir(base_dir: Path) -> None:
    """Setează HIDROELECTRICA_DIR — mereu /config/hidroelectrica (legacy compat)."""
    legacy = Path(base_dir)
    if legacy.name != "hidroelectrica":
        parent = legacy.parent if legacy.parent.name == "hidroelectrica" else legacy
        legacy = parent if parent.name == "hidroelectrica" else Path("/config/hidroelectrica")
    legacy = legacy.resolve()
    os.environ["HIDROELECTRICA_DIR"] = str(legacy)
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "logs").mkdir(exist_ok=True)
    (legacy / "invoices").mkdir(exist_ok=True)
    (legacy / "browser_profile").mkdir(exist_ok=True)
    from . import config as cfg

    cfg.BASE_DIR = cfg.resolve_base_dir()
    cfg.SESSION_FILE = cfg.BASE_DIR / "session.json"
    cfg.HEALTH_FILE = cfg.BASE_DIR / "health.json"
    cfg.SECRETS_FILE = cfg.BASE_DIR / "secrets.json"
    cfg.DATA_FILE = cfg.BASE_DIR / "data.json"
    cfg.COOKIES_IMPORT_FILE = cfg.BASE_DIR / "cookies_import.json"
    cfg.TOKEN_FILE = cfg.BASE_DIR / "token.txt"
    cfg.INVOICES_DIR = cfg.BASE_DIR / "invoices"
    cfg.LOGS_DIR = cfg.BASE_DIR / "logs"
    cfg.BROWSER_PROFILE = cfg.BASE_DIR / "browser_profile"
