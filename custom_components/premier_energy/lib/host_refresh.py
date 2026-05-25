"""Refresh token Premier pe HOST când Chromium eșuează în containerul HA OS."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

HA_HOST = "172.30.32.1"
SSH_KEY = Path("/config/.ssh/ha_to_host")
KNOWN_HOSTS = Path("/config/.ssh/known_hosts")
REFRESH_SCRIPT = Path("/config/premier_energy/refresh_token_simple.py")
VENV_PYTHON = Path("/config/premier_energy/venv/bin/python3")


def in_ha_container() -> bool:
    return Path("/.dockerenv").exists()


def host_ssh_available() -> bool:
    return in_ha_container() and SSH_KEY.is_file()


def refresh_via_host() -> bool:
    """Rulează refresh_token_simple.py pe host prin SSH (Chromium funcționează acolo)."""
    if not host_ssh_available():
        return False
    if not REFRESH_SCRIPT.is_file() or not VENV_PYTHON.is_file():
        _LOGGER.warning("Lipsește %s sau venv — vezi scripts/setup-ha-premier-host-ssh.sh", REFRESH_SCRIPT)
        return False
    cmd = [
        "ssh",
        "-i",
        str(SSH_KEY),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=" + str(KNOWN_HOSTS),
        f"root@{HA_HOST}",
        f"{VENV_PYTHON} {REFRESH_SCRIPT}",
    ]
    try:
        KNOWN_HOSTS.parent.mkdir(parents=True, exist_ok=True)
        KNOWN_HOSTS.touch(exist_ok=True)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            _LOGGER.error("Host refresh failed: %s", (r.stderr or r.stdout)[:500])
            return False
        _LOGGER.info("Premier token refreshed via host SSH")
        return True
    except Exception as exc:
        _LOGGER.error("Host SSH refresh: %s", exc)
        return False
