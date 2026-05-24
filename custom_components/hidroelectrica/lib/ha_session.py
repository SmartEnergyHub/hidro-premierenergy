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

    if allow_auto_login:
        from .auto_login_core import auto_login_sync

        if auto_login_sync() and _validate_with_retries(tries=2, delay=1.0):
            return True

    if cookies_import_is_fresher() and try_recover_session():
        return _validate_with_retries(tries=2, delay=1.0)

    return False


def setup_storage_dir(base_dir: Path) -> None:
    os.environ["HIDROELECTRICA_DIR"] = str(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "logs").mkdir(exist_ok=True)
    (base_dir / "invoices").mkdir(exist_ok=True)
    (base_dir / "browser_profile").mkdir(exist_ok=True)
