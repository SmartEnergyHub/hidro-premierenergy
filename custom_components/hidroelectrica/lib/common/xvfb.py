"""Pornește Xvfb pentru browser headed pe HAOS (fără ecran fizic)."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

DISPLAY = os.environ.get("ENERGIE_DISPLAY", ":99")
XVFB_BIN = Path("/usr/bin/Xvfb")
PID_FILE = Path("/config/.xvfb.pid")


def ensure_xvfb(display: str = DISPLAY) -> str:
    """Returnează DISPLAY activ; pornește Xvfb dacă lipsește."""
    os.environ["DISPLAY"] = display
    if _display_alive(display):
        return display
    if not XVFB_BIN.is_file():
        raise FileNotFoundError(f"Xvfb negăsit: {XVFB_BIN}")
    proc = subprocess.Popen(
        [str(XVFB_BIN), display, "-screen", "0", "1920x1080x24", "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    for _ in range(20):
        if _display_alive(display):
            return display
        time.sleep(0.25)
    raise RuntimeError(f"Xvfb nu a pornit pe {display}")


def _display_alive(display: str) -> bool:
    try:
        r = subprocess.run(
            ["pgrep", "-x", "Xvfb"],
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0 and os.environ.get("DISPLAY") == display or _test_display(display)
    except Exception:
        return False


def _test_display(display: str) -> bool:
    try:
        r = subprocess.run(
            ["sh", "-c", f"DISPLAY={display} xdpyinfo >/dev/null 2>&1"],
            timeout=5,
        )
        return r.returncode == 0
    except Exception:
        # xdpyinfo poate lipsi pe Alpine — verificăm doar proces
        try:
            r = subprocess.run(["pgrep", "-x", "Xvfb"], capture_output=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False
