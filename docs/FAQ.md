# FAQ

## General

### Do I need to export cookies or tokens manually?
**No.** Enter credentials once in Config Flow. Everything else is automatic.

### Can I use both integrations together?
**Yes.** They share a Chromium lock so only one browser runs at a time — this is intentional.

### Does this work on Home Assistant OS?
**Yes.** HA OS includes Chromium, ChromeDriver, and Xvfb required for Hidroelectrica.

## Premier Energy

### Why does login use a browser?
Premier uses Azure AD B2C OAuth. The integration automates the same flow as the web portal and stores the JWT.

### How often is the token refreshed?
Every 10 minutes. Browser opens only when the JWT expires within ~20 minutes.

## Hidroelectrica

### Why Xvfb?
reCAPTCHA v3 blocks headless browsers. The integration uses a virtual display (Xvfb) with a real headed Chromium — fully automatic.

### What if session fails?
The coordinator retries auto-login up to 3 times. Use the **Force login** button or `hidroelectrica.force_login` service.

## HACS

### One repo or two integrations?
This repository contains **both** integrations under `custom_components/`. HACS installs the repo once; you add each integration separately in HA UI.

## Migration

### Can I keep my old shell_command setup?
Yes, during testing. See [MIGRATION.md](MIGRATION.md). Disable legacy YAML automations when satisfied.
