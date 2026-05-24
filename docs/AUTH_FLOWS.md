# Auth Flows

## Premier Energy

1. User enters email + password in Config Flow
2. Validation: Selenium opens `my.premierenergy.ro`
3. Azure B2C login form → submit
4. Extract `id_token` from `localStorage`
5. Save to `token.txt` + browser profile retains OAuth state
6. Every 10 min coordinator checks JWT `exp`
7. If valid > 20 min margin → API only (no browser)
8. Else → browser re-opens profile, re-login if needed

**API auth header:** `Premier-Auth: Bearer <JWT>`

## Hidroelectrica

1. User enters username + password in Config Flow
2. `ensure_session()` validates `BillingHistory.aspx`
3. If login page → `auto_login_core`:
   - Start Xvfb `:99`
   - Headed Chromium (NOT headless — reCAPTCHA blocks headless)
   - Execute reCAPTCHA v3 `grecaptcha.execute`
   - Submit login form
4. Save cookies + CSRF to `session.json`
5. Every 5 min: ping portal (extends ASP.NET session)
6. On failure: auto-login retry (3x) with persistent profile

**Never overwrites** stale `cookies_import.json` — manual import optional only.

## Security

- Passwords stored in HA Config Entry (encrypted at rest)
- Diagnostics redact passwords/tokens/cookies
- `secrets.json` mirror chmod 600 for legacy lib compatibility
