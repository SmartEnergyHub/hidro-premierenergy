"""Gestionare sesiune cookies + requests."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from .backup import backup_files, log_change
from .config import (
    PORTAL_BASE,
    SESSION_MARGIN_HOURS,
    resolve_base_dir,
)
from .logging_util import setup_logger

log = setup_logger("hidro.session")


def _session_file() -> Path:
    return resolve_base_dir() / "session.json"


def _token_file() -> Path:
    return resolve_base_dir() / "token.txt"


def _cookies_import_file() -> Path:
    return resolve_base_dir() / "cookies_import.json"


def load_secrets() -> dict[str, str]:
    from .config import SECRETS_FILE

    data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    return {
        "username": (data.get("username") or data.get("user") or "").strip(),
        "password": (data.get("password") or "").strip(),
        "telegram_bot_token": (data.get("telegram_bot_token") or "").strip(),
        "telegram_chat_id": (data.get("telegram_chat_id") or "").strip(),
        "pod": (data.get("pod") or "").strip(),
        "contract": (data.get("contract") or "").strip(),
        "account_number": (data.get("account_number") or data.get("cont") or "").strip(),
    }


def load_session() -> dict[str, Any] | None:
    path = _session_file()
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("session.json invalid: %s", exc)
        return None


def save_session(
    cookies: list[dict[str, Any]],
    csrf: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    path = _session_file()
    if path.is_file():
        backup_files([path], label="pre_session_save")
    payload: dict[str, Any] = {
        "saved_at": time.time(),
        "cookies": cookies,
        "csrf": csrf,
    }
    if extra:
        payload.update(extra)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if csrf:
        _token_file().write_text(csrf, encoding="utf-8")
    log_change("SESSION saved")
    log.info("Session saved (%d cookies)", len(cookies))


def session_expired(session: dict[str, Any]) -> bool:
    saved = session.get("saved_at", 0)
    age_hours = (time.time() - saved) / 3600
    return age_hours > (24 * 7 - SESSION_MARGIN_HOURS)


def requests_session_from_store(session: dict[str, Any] | None = None) -> requests.Session:
    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
            "Accept-Language": "ro-RO,ro;q=0.9",
        }
    )
    store = session or load_session()
    if not store:
        return sess
    for c in store.get("cookies", []):
        try:
            sess.cookies.set(
                c["name"],
                c["value"],
                domain=c.get("domain"),
                path=c.get("path", "/"),
            )
        except Exception as exc:
            log.debug("cookie skip %s: %s", c.get("name"), exc)
    csrf = store.get("csrf") or ""
    if csrf:
        sess.headers["X-CSRF-Token"] = csrf
    return sess


def is_login_page(html: str, url: str) -> bool:
    low = (html or "").lower()
    if "txtlogin" in low and "txtpwd" in low and "btnlogin" in low:
        return True
    if "nume de utilizator" in low and "parola" in low and "btnlogin" in low:
        return True
    if url.rstrip("/").endswith("/portal") or url.rstrip("/").endswith("/portal/"):
        if "autentificare" in low or "sign in" in low:
            return True
    # Pagina de login ASP.NET returnează ~43KB; billing autentificat >100KB
    if len(html or "") < 80000 and "btnlogin" in low:
        return True
    return False


def is_authenticated_page(html: str) -> bool:
    if is_login_page(html, ""):
        return False
    low = (html or "").lower()
    if "hdncsrftoken" in low and any(
        m in low for m in ("billinghistory", "indexhistory", "dashboard.aspx", "logout", "deconect")
    ):
        return True
    strong_markers = (
        "logout",
        "log out",
        "deconect",
        "sign out",
        "lblaccountname",
        "welcome,",
        "bun venit",
        "account summary",
        "sumar cont",
    )
    return any(m in low for m in strong_markers)


def export_cookies(http: requests.Session) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in http.cookies:
        out.append(
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain or "ihidro.ro",
                "path": c.path or "/",
            }
        )
    return out


def touch_session(http: requests.Session, html: str) -> bool:
    """Salvează cookies/CSRF după un request reușit — prelungește sesiunea pe server."""
    if not is_authenticated_page(html):
        return False
    store = load_session() or {}
    csrf = extract_csrf_from_html(html) or store.get("csrf", "")
    cookies = export_cookies(http)
    if not cookies:
        cookies = store.get("cookies", [])
    save_session(
        cookies,
        csrf=csrf,
        extra={
            "source": store.get("source", "keepalive"),
            "imported_at": store.get("imported_at"),
            "last_keepalive": time.time(),
        },
    )
    return True


def cookies_import_is_fresher() -> bool:
    imp = _cookies_import_file()
    if not imp.is_file():
        return False
    imp_mtime = imp.stat().st_mtime
    store = load_session()
    if not store:
        return True
    saved = float(store.get("saved_at") or store.get("imported_at") or 0)
    return imp_mtime > saved


def _session_from_cookies(cookies: list[dict[str, Any]], csrf: str = "") -> requests.Session:
    store = {"cookies": cookies, "csrf": csrf}
    return requests_session_from_store(store)


def try_recover_session(http: requests.Session | None = None) -> bool:
    imp = _cookies_import_file()
    if not imp.is_file():
        return False
    if not cookies_import_is_fresher():
        log.info(
            "Skip recovery: cookies_import.json mai vechi decât session.json — "
            "nu suprascriu sesiunea activă"
        )
        return False
    try:
        import_cookies_from_json(imp)
        log.info("Sesiune recuperată din cookies_import.json")
        return True
    except Exception as exc:
        log.warning("Recovery cookies_import eșuat: %s", exc)
        return False


def validate_session(sess: requests.Session | None = None, *, touch: bool = True) -> bool:
    http = sess or requests_session_from_store()
    url = f"{PORTAL_BASE}/BillingHistory.aspx"
    try:
        r = http.get(url, timeout=30, allow_redirects=True)
        log.debug("validate BillingHistory -> %s len=%s", r.status_code, len(r.text))
        if r.status_code != 200:
            return False
        if is_login_page(r.text, r.url):
            log.info("Session invalid — login page detected (len=%s)", len(r.text))
            return False
        csrf = extract_csrf_from_html(r.text)
        if csrf or is_authenticated_page(r.text):
            if touch:
                touch_session(http, r.text)
            log.info("Session valid via BillingHistory.aspx")
            return True
    except Exception as exc:
        log.debug("validate error: %s", exc)
    return False


def import_cookies_from_json(path: Path) -> None:
    """Import cookies: format Selenium list sau {cookies:[...]}. Validează înainte de save."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "cookies" in raw:
        cookies = raw["cookies"]
        csrf = raw.get("csrf", "")
    elif isinstance(raw, list):
        cookies = raw
        csrf = ""
    else:
        raise ValueError("Format cookies necunoscut")

    http = _session_from_cookies(cookies, csrf)
    if not csrf:
        try:
            r = http.get(f"{PORTAL_BASE}/BillingHistory.aspx", timeout=60)
            csrf = extract_csrf_from_html(r.text)
            if csrf:
                http.headers["X-CSRF-Token"] = csrf
        except Exception as exc:
            log.debug("csrf fetch: %s", exc)
    if not validate_session(http, touch=False):
        raise RuntimeError(
            "Cookies importate dar sesiunea nu e validă — reexportă din browser logat"
        )

    save_session(
        cookies,
        csrf=csrf,
        extra={"source": "import", "imported_at": time.time()},
    )


def cookies_from_selenium(driver) -> list[dict[str, Any]]:
    return driver.get_cookies()


def extract_csrf_from_html(html: str) -> str:
    import re

    m = re.search(r'id="hdnCSRFToken"[^>]*value="([^"]+)"', html, re.I)
    if m:
        return m.group(1)
    m = re.search(r'name="hdnCSRFToken"[^>]*value="([^"]+)"', html, re.I)
    return m.group(1) if m else ""
