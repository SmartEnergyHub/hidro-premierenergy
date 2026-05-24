"""Backup și rollback fișiere înainte de modificări."""

from __future__ import annotations

import json
import shutil
import time
from collections.abc import Iterable
from pathlib import Path

from .config import BACKUPS_DIR, BASE_DIR, CHANGELOG_FILE


def _ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def log_change(message: str) -> None:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n"
    with CHANGELOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line)


def backup_files(paths: Iterable[Path], label: str = "manual") -> Path:
    """Copie timestamped; returnează directorul backup."""
    dest = BACKUPS_DIR / f"{label}_{_ts()}"
    dest.mkdir(parents=True, exist_ok=True)
    manifest: list[str] = []
    for src in paths:
        src = Path(src)
        if not src.exists():
            continue
        rel = src.relative_to(BASE_DIR) if src.is_relative_to(BASE_DIR) else src.name
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
        else:
            shutil.copy2(src, target)
        manifest.append(str(rel))
    (dest / "manifest.json").write_text(
        json.dumps({"label": label, "files": manifest}, indent=2),
        encoding="utf-8",
    )
    log_change(f"BACKUP {label} -> {dest} ({len(manifest)} items)")
    return dest


def rollback(backup_dir: Path) -> None:
    backup_dir = Path(backup_dir)
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest lipsă: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel in manifest.get("files", []):
        src = backup_dir / rel
        dst = BASE_DIR / rel
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    log_change(f"ROLLBACK from {backup_dir}")


def safe_write(path: Path, content: str, backup: bool = True) -> None:
    path = Path(path)
    if backup and path.is_file():
        backup_files([path], label=f"pre_write_{path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    log_change(f"WRITE {path}")
