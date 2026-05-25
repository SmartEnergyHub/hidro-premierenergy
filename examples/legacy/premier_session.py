#!/usr/bin/env python3
"""Premier Energy — ensure token (refresh pe HOST via SSH când rulezi în containerul HA)."""
from __future__ import annotations

import base64
import json
import subprocess
import time
from pathlib import Path

import requests

BASE = Path("/config/premier_energy")
API = "https://peremierenergy-portalclient.azurewebsites.net/api"
PY = str(BASE / "venv/bin/python3")
REFRESH = str(BASE / "refresh_token_simple.py")
HOST = "172.30.32.1"
SSH_KEY = Path("/config/.ssh/ha_to_host")


def entry_dirs() -> list[Path]:
    out = [BASE]
    if BASE.is_dir():
        for child in BASE.iterdir():
            if child.is_dir() and (child / "token.txt").is_file():
                out.append(child)
    return out


def token_paths() -> list[Path]:
    paths: list[Path] = []
    for d in entry_dirs():
        p = d / "token.txt"
        if p not in paths:
            paths.append(p)
    return paths


def data_paths() -> list[Path]:
    paths: list[Path] = []
    for d in entry_dirs():
        p = d / "data.json"
        if p.is_file() and p not in paths:
            paths.append(p)
    if (BASE / "data.json").is_file():
        paths.insert(0, BASE / "data.json")
    return paths


def read_token() -> str:
    for p in token_paths():
        if p.is_file():
            t = p.read_text(encoding="utf-8").strip()
            if t:
                return t
    return ""


def jwt_ok(token: str, margin: int = 300) -> bool:
    try:
        part = token.split(".")[1]
        pad = "=" * (-len(part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(part + pad).decode())
        exp = payload.get("exp")
        return isinstance(exp, (int, float)) and (exp - time.time()) > margin
    except Exception:
        return False


def api_ok(token: str) -> bool:
    try:
        r = requests.get(
            f"{API}/locConsum?cuAdresa=true",
            headers={"Premier-Auth": f"Bearer {token}"},
            timeout=20,
        )
        return r.status_code == 200
    except Exception:
        return False


def refresh_token() -> None:
    in_docker = Path("/.dockerenv").exists()
    if in_docker and SSH_KEY.is_file():
        cmd = [
            "ssh",
            "-i",
            str(SSH_KEY),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/config/.ssh/known_hosts",
            f"root@{HOST}",
            f"{PY} {REFRESH}",
        ]
    else:
        cmd = [PY, REFRESH]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout or "refresh failed")


def ensure_token() -> str:
    token = read_token()
    if token and jwt_ok(token) and api_ok(token):
        return token
    refresh_token()
    token = read_token()
    if not token:
        raise RuntimeError("Token lipsă după refresh")
    return token


def load_secrets() -> dict:
    f = BASE / "secrets.json"
    if f.is_file():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}


def load_data() -> dict:
    for p in data_paths():
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    return {}


def headers(token: str | None = None) -> dict[str, str]:
    t = token or ensure_token()
    return {"Premier-Auth": f"Bearer {t}", "Accept": "application/json"}


if __name__ == "__main__":
    print("TOKEN_OK", ensure_token()[:12] + "...")
