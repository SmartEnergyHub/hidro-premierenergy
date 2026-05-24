"""Parsare HTML portal iHidro."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any


def _clean_num(s: str) -> float | None:
    if not s:
        return None
    s = s.replace("\xa0", " ").strip()
    s = re.sub(r"[^\d,.\-]", "", s)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _iso_date(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], fmt).replace(tzinfo=UTC).isoformat()
        except ValueError:
            pass
    return text


def parse_portal_pages(pages: dict[str, str]) -> dict[str, Any]:
    data: dict[str, Any] = {
        "updated_at": datetime.now(UTC).isoformat(),
        "loc_consum": "",
        "pod": "",
        "contract": "",
        "adresa": "",
        "sold": None,
        "ultima_factura": {},
        "facturi": [],
        "consum": {
            "media_lunara_lei": None,
            "maxim_an_lei": None,
            "curent_kwh": None,
            "perioada": "",
            "conventie_lunara": {},
        },
        "index": {
            "curent": None,
            "ultima_citire": "",
            "ultim_index_distributie": None,
            "perioada_transmitere_start": "",
            "perioada_transmitere_stop": "",
            "autocitire_activa": False,
            "tip_citire": "",
        },
        "index_istoric": [],
        "session_valid": True,
    }

    combined = "\n".join(pages.values())

    # POD numeric (26 cifre din capturi)
    m = re.search(r"\b(5940106000[0-9]{14,18})\b", combined)
    if m:
        data["pod"] = m.group(1)

    # Perioadă autocitire din SelfMeterReading
    if "self_meter" in pages:
        sm = pages["self_meter"]
        m1 = re.search(r'id="hdnopendate"[^>]*value="([^"]+)"', sm, re.I)
        m2 = re.search(r'id="hdnclosedate"[^>]*value="([^"]+)"', sm, re.I)
        if m1:
            data["index"]["perioada_transmitere_start"] = _iso_date(m1.group(1))
        if m2:
            data["index"]["perioada_transmitere_stop"] = _iso_date(m2.group(1))
        m_last = re.search(
            r"Ultim(?:ul|a)\s+index[^0-9]*([0-9]{4,6})",
            re.sub(r"<[^>]+>", " ", sm),
            re.I,
        )
        if m_last:
            data["index"]["ultim_index_distributie"] = int(m_last.group(1))

    # Usages — medie lunară
    if "usages" in pages:
        u = pages["usages"]
        m = re.search(r"MEDIA\s+LUNAR[AĂ][^0-9]*([0-9][0-9.,]+)", u, re.I)
        if m:
            data["consum"]["media_lunara_lei"] = _clean_num(m.group(1))
        m = re.search(r"MAXIMUL\s+ULTIMULUI\s+AN[^0-9]*([0-9][0-9.,]+)", u, re.I)
        if m:
            data["consum"]["maxim_an_lei"] = _clean_num(m.group(1))

    # Convenție consum kWh/lună
    if "convention" in pages:
        conv = pages["convention"]
        luni = (
            "ianuarie",
            "februarie",
            "martie",
            "aprilie",
            "mai",
            "iunie",
            "iulie",
            "august",
            "septembrie",
            "octombrie",
            "noiembrie",
            "decembrie",
        )
        conventie = {}
        text = re.sub(r"<[^>]+>", "\n", conv)
        for luna in luni:
            pat = rf"{luna}[^0-9]*([0-9]+)\s*kWh"
            m = re.search(pat, text, re.I)
            if m:
                conventie[luna] = int(m.group(1))
        if conventie:
            data["consum"]["conventie_lunara"] = conventie

    # Autocitire activă
    if data["index"]["perioada_transmitere_start"] and data["index"]["perioada_transmitere_stop"]:
        try:
            start = datetime.fromisoformat(
                data["index"]["perioada_transmitere_start"].replace("Z", "+00:00")
            )
            stop = datetime.fromisoformat(
                data["index"]["perioada_transmitere_stop"].replace("Z", "+00:00")
            )
            if start > stop:
                start, stop = stop, start
                data["index"]["perioada_transmitere_start"] = start.isoformat()
                data["index"]["perioada_transmitere_stop"] = stop.isoformat()
            now = datetime.now(UTC)
            data["index"]["autocitire_activa"] = start <= now <= stop.replace(hour=23, minute=59)
        except Exception:
            pass

    return data


def merge_api_index_rows(data: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    data["index_istoric"] = rows
    latest = max(rows, key=lambda r: r.get("Date", ""))
    data["index"]["curent"] = int(str(latest.get("Index", "0")).replace(",", "") or 0)
    data["index"]["ultima_citire"] = latest.get("Date", "")
    data["index"]["tip_citire"] = latest.get("ReadingType", "")
    if latest.get("POD"):
        data["pod"] = latest.get("POD")
