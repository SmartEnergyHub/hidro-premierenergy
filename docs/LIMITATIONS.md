# Known Limitations

1. **Chromium required** — HA OS includes it; generic Docker may not
2. **Xvfb required for Hidro** — reCAPTCHA v3 detects headless automation
3. **Selenium sync in executor** — brief CPU spikes during login (~30–60s)
4. **Single concurrent browser** — global lock between Premier and Hidro
5. **Premier PDF** — depends on API endpoint availability; may need extension
6. **send_index** — necesită `input_number.hidro_index_curent` / `input_number.index_gaz_premier` sau argument la `/indexhidro` / `/indexgaze`
7. **Telegram** — optional in Hidro config; use HA notify for production
8. **Provider ToS** — automation may violate terms; use at your own risk
9. **reCAPTCHA changes** — Hidro may break if Google/site changes captcha policy
