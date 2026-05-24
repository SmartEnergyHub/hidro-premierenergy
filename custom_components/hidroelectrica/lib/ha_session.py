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

    # cookies_import DOAR dacă e mai nou decât session activă
    if cookies_import_is_fresher() and try_recover_session():
        return _validate_with_retries(tries=2, delay=1.0)

    return False


def setup_storage_dir(base_dir: Path) -> None:
    """Setează HIDROELECTRICA_DIR — preferă /config/hidroelectrica (legacy)."""
    domain_dir = "hidroelectrica"
    legacy = base_dir
    if base_dir.name != domain_dir:
        legacy = base_dir.parent if base_dir.parent.name == domain_dir else base_dir
    os.environ["HIDROELECTRICA_DIR"] = str(legacy)
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "logs").mkdir(exist_ok=True)
    (legacy / "invoices").mkdir(exist_ok=True)
    (legacy / "browser_profile").mkdir(exist_ok=True)
    # Reîncarcă căile modulului config după schimbarea env
    from . import config as cfg

    cfg.BASE_DIR = cfg.resolve_base_dir()
    cfg.SESSION_FILE = cfg.BASE_DIR / "session.json"
    cfg.HEALTH_FILE = cfg.BASE_DIR / "health.json"
    cfg.SECRETS_FILE = cfg.BASE_DIR / "secrets.json"
    cfg.DATA_FILE = cfg.BASE_DIR / "data.json"
    cfg.COOKIES_IMPORT_FILE = cfg.BASE_DIR / "cookies_import.json"
