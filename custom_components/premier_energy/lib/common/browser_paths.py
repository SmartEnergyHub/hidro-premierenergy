"""Chromium / ChromeDriver resolution inside the Home Assistant container."""

from __future__ import annotations

import os
from pathlib import Path

INSTALL_HINT = "docker exec homeassistant apk add --no-cache chromium chromium-chromedriver xvfb"


class BrowserDepsMissingError(RuntimeError):
    """Raised when Selenium cannot find Chromium or ChromeDriver in the HA container."""


def _first_existing(candidates: tuple[str | None, ...]) -> str | None:
    for path in candidates:
        if path and Path(path).is_file():
            return path
    return None


def resolve_chromium_bin() -> str:
    path = _first_existing(
        (
            os.environ.get("CHROMIUM_PATH"),
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/lib/chromium/chromium",
        )
    )
    if not path:
        raise BrowserDepsMissingError(
            f"Chromium lipsește din containerul Home Assistant. Rulează: {INSTALL_HINT}"
        )
    return path


def resolve_chromedriver() -> str:
    path = _first_existing(
        (
            os.environ.get("CHROMEDRIVER_PATH"),
            "/usr/bin/chromedriver",
            "/usr/lib/chromium/chromedriver",
        )
    )
    if not path:
        raise BrowserDepsMissingError(
            f"ChromeDriver lipsește din containerul Home Assistant. Rulează: {INSTALL_HINT}"
        )
    return path


def ensure_browser_deps(*, require_xvfb: bool = False) -> tuple[str, str]:
    chromium = resolve_chromium_bin()
    chromedriver = resolve_chromedriver()
    if require_xvfb:
        xvfb = _first_existing((os.environ.get("XVFB_PATH"), "/usr/bin/Xvfb"))
        if not xvfb:
            raise BrowserDepsMissingError(
                f"Xvfb lipsește din containerul Home Assistant. Rulează: {INSTALL_HINT}"
            )
    return chromium, chromedriver


def is_browser_deps_error(exc: BaseException) -> bool:
    if isinstance(exc, BrowserDepsMissingError):
        return True
    msg = str(exc).lower()
    return "nosuchdriver" in msg or "chromedriver" in msg or "chromium" in msg
