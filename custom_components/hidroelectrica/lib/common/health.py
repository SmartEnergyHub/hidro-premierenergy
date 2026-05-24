"""Health state JSON — senzori HA + debug."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def read_health(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "unknown", "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "error", "updated_at": None}


def write_health(path: Path, status: str, **fields: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "status": status,
        "updated_at": time.time(),
        "updated_at_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        **fields,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
