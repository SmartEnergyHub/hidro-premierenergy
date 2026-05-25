"""Support, donate links, debug bundle — fără secrete în output."""

from __future__ import annotations

import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

URL_DONATE = "https://paypal.me/solovip"
URL_GITHUB = "https://github.com/SmartEnergyHub/hidro-premierenergy"
URL_ISSUES = "https://github.com/SmartEnergyHub/hidro-premierenergy/issues/new/choose"
URL_DISCUSSIONS = "https://github.com/SmartEnergyHub/hidro-premierenergy/discussions"
URL_DOCS = "https://github.com/SmartEnergyHub/hidro-premierenergy/blob/main/docs/INSTALLATION.md"
URL_SUPPORT = "https://github.com/SmartEnergyHub/hidro-premierenergy/blob/main/SUPPORT.md"

SUPPORT_LINKS: dict[str, str] = {
    "donate": URL_DONATE,
    "github": URL_GITHUB,
    "issues": URL_ISSUES,
    "discussions": URL_DISCUSSIONS,
    "docs": URL_DOCS,
    "support": URL_SUPPORT,
    "feature_request": "https://github.com/SmartEnergyHub/hidro-premierenergy/issues/new?template=feature_request.yml",
    "bug_report": "https://github.com/SmartEnergyHub/hidro-premierenergy/issues/new?template=bug_report.yml",
    "auth_issue": "https://github.com/SmartEnergyHub/hidro-premierenergy/issues/new?template=auth_issue.yml",
    "provider_change": "https://github.com/SmartEnergyHub/hidro-premierenergy/issues/new?template=provider_change.yml",
}

NOTIFICATIONS: dict[str, tuple[str, str]] = {
    "donate": (
        "SmartEnergyHub — Mulțumim! ❤️",
        "Integrările HA Energie România rămân **gratuite**. Contribuția ta este voluntară "
        "și susține mentenanța, testarea și noile funcții.\n\n"
        "👉 [Deschide pagina securizată de donație]({url})",
    ),
    "github": (
        "Premier Energy — GitHub",
        "Cod sursă, release-uri și changelog:\n\n[Deschide repository]({url})",
    ),
    "support": (
        "Premier Energy — Support",
        "Ghid instalare, depanare și export debug:\n\n[Deschide SUPPORT.md]({url})",
    ),
    "discussions": (
        "Premier Energy — Discussions",
        "Întrebări, idei și feedback comunitate:\n\n[Deschide Discussions]({url})",
    ),
    "issues": (
        "Premier Energy — Issues",
        "Raportează o problemă sau cere o funcție:\n\n[Deschide Issues]({url})",
    ),
    "bug_report": (
        "Premier Energy — Bug report",
        "Template pentru raportare bug:\n\n[Deschide formular]({url})",
    ),
    "auth_issue": (
        "Premier Energy — Autentificare",
        "Probleme login / token / sesiune:\n\n[Deschide formular]({url})",
    ),
    "feature_request": (
        "Premier Energy — Feature request",
        "Propune o îmbunătățire:\n\n[Deschide formular]({url})",
    ),
    "provider_change": (
        "Premier Energy — Schimbare portal",
        "Schimbări API / portal furnizor:\n\n[Deschide formular]({url})",
    ),
}

DONATE_ENTITY_ICON = "https://raw.githubusercontent.com/SmartEnergyHub/hidro-premierenergy/main/assets/branding/donate-icon.svg"


def notification_content(link_key: str, url: str) -> tuple[str, str]:
    title, template = NOTIFICATIONS.get(
        link_key,
        ("Premier Energy — Support", "[Deschide link-ul]({url})"),
    )
    return title, template.format(url=url)


_REDACT_PATTERNS = (
    (re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), "[REDACTED_JWT]"),
    (re.compile(r"ghp_[A-Za-z0-9]+"), "[REDACTED_TOKEN]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[REDACTED_EMAIL]"),
    (re.compile(r'"password"\s*:\s*"[^"]*"', re.I), '"password": "[REDACTED]"'),
)


def redact_text(text: str) -> str:
    out = text
    for pattern, repl in _REDACT_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def redact_dict(data: Any) -> Any:
    if isinstance(data, dict):
        skip_keys = {
            "password",
            "token",
            "id_token",
            "csrf",
            "cookies",
            "telegram_bot_token",
            "telegram_chat_id",
            "email",
            "username",
        }
        return {
            k: "[REDACTED]" if k.lower() in skip_keys else redact_dict(v) for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact_dict(x) for x in data]
    if isinstance(data, str):
        return redact_text(data) if len(data) > 6 else data
    return data


def build_support_bundle(
    config_dir: Path,
    integration: str,
    entry_id: str,
    debug_info: dict[str, Any],
    log_grep: str = "",
) -> Path:
    out_dir = config_dir / "support_bundles"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    zip_path = out_dir / f"{integration}_{entry_id[:8]}_{ts}.zip"

    payload = {
        "integration": integration,
        "entry_id": entry_id,
        "generated_at": ts,
        "debug": redact_dict(debug_info),
    }

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("diagnostics.json", json.dumps(payload, indent=2, ensure_ascii=False))
        if log_grep:
            zf.writestr("logs_excerpt.txt", redact_text(log_grep[:50000]))
        legacy_health = config_dir / "premier_energy" / "health.json"
        if legacy_health.is_file():
            zf.writestr(
                "health.json", redact_text(legacy_health.read_text(encoding="utf-8")[:20000])
            )
    return zip_path
