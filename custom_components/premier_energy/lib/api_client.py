"""Premier Energy REST API client."""

from __future__ import annotations

import logging
from typing import Any

import requests

from ..const import API_BASE

_LOGGER = logging.getLogger(__name__)


class PremierApiClient:
    """Sync API client — uses Bearer token from auth manager."""

    def __init__(self, token: str) -> None:
        self._headers = {
            "Premier-Auth": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _get(self, path: str) -> Any:
        url = f"{API_BASE}/{path.lstrip('/')}"
        r = requests.get(url, headers=self._headers, timeout=30)
        r.raise_for_status()
        return r.json()

    def fetch_all(self) -> dict[str, Any]:
        facturi = self._get("facturi?Versiunea=1")
        consum = self._get("consum")
        locuri = self._get("locConsum?cuAdresa=true")

        ultima = facturi[0] if facturi else {}
        consum_row = {}
        if consum and consum[0].get("contracte"):
            c0 = consum[0]["contracte"][0]
            if c0.get("consum"):
                consum_row = c0["consum"][0]
        loc = locuri[0] if locuri else {}

        return {
            "ultima_factura_suma": ultima.get("TOTAL_AMNT"),
            "numar_factura": ultima.get("OPBEL"),
            "scadenta": ultima.get("FAEDN"),
            "consum_m3": consum_row.get("consumM3"),
            "consum_mwh": consum_row.get("consumMWH"),
            "adresa": loc.get("Adresa"),
            "citire_start": loc.get("perioada_citire_start"),
            "citire_stop": loc.get("perioada_citire_sfarsit"),
            "facturi": facturi,
            "consum_raw": consum,
            "locuri": locuri,
            "session_valid": True,
        }

    def download_invoice_pdf(self, invoice_number: str, dest_dir) -> str | None:
        """Download invoice PDF if API supports it."""
        try:
            data = self._get(f"facturi/pdf?OPBEL={invoice_number}")
            if isinstance(data, dict) and data.get("url"):
                pdf = requests.get(data["url"], timeout=90)
                pdf.raise_for_status()
                path = dest_dir / f"{invoice_number}.pdf"
                path.write_bytes(pdf.content)
                return str(path)
        except Exception as exc:
            _LOGGER.debug("PDF download fallback: %s", exc)
        return None
