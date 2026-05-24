# Instalare — Premier Energy & Hidroelectrica

Ghid complet pentru **Home Assistant OS** (recomandat: Raspberry Pi 4/5, x86 mini-PC).

| Integrare | Furnizor | Tip utilitate | Portal |
|-----------|----------|---------------|--------|
| **Premier Energy** | Premier Energy | **Gaze naturale** | [my.premierenergy.ro](https://my.premierenergy.ro) |
| **Hidroelectrica** | Hidroelectrica | **Energie electrică** | [ihidro.ro/portal](https://ihidro.ro/portal/) |

Ambele integrări sunt **FULL AUTO**: introduci user/parolă o singură dată în UI; token JWT (Premier) sau sesiune + cookies (Hidro) se reînnoiesc automat.

---

## 1. Cerințe prealabile

### Home Assistant

| Componentă | Versiune minimă |
|------------|-----------------|
| Home Assistant Core | **2024.12.0** |
| HACS | **1.34.0** (dacă instalezi via HACS) |
| Python | 3.11+ (inclus în HA) |

### Platforme suportate

| Platformă | Premier Energy | Hidroelectrica | Note |
|-----------|:--------------:|:--------------:|------|
| **Home Assistant OS** | ✅ | ✅ | Recomandat |
| Supervised | ✅ | ✅ | |
| Container Docker | ⚠️ | ⚠️ | Trebuie Chromium + Xvfb în container |
| Core (venv manual) | ⚠️ | ⚠️ | Instalare manuală browser |

| Arhitectură | Suport |
|-------------|--------|
| Raspberry Pi (ARM64) | ✅ |
| x86-64 | ✅ |

### Dependențe sistem (browser automation)

Integrările folosesc **Selenium + Chromium** pentru login automat (Azure B2C / reCAPTCHA).

| Pachet / binar | Premier Energy (gaze naturale) | Hidroelectrica (energie electrică) | Cale tipică pe HA OS |
|----------------|:------------------------------:|:----------------------------------:|----------------------|
| **Chromium** | ✅ obligatoriu | ✅ obligatoriu | `/usr/bin/chromium` |
| **ChromeDriver** | ✅ obligatoriu | ✅ obligatoriu | `/usr/bin/chromedriver` |
| **Xvfb** | opțional | ✅ **obligatoriu** | `/usr/bin/Xvfb` |
| **DISPLAY** | setat automat de Xvfb | setat automat de Xvfb | `:99` |

> **De ce Xvfb la Hidroelectrica?** Portalul iHidro folosește **reCAPTCHA** care blochează Chromium headless. Integrarea pornește un display virtual (Xvfb) și rulează browser **headed** — fără monitor fizic.

### Dependențe Python (instalate automat de HA)

Declarate în `manifest.json` — **nu instala manual** în venv:

| Pachet | Versiune |
|--------|----------|
| `requests` | ≥ 2.31.0 |
| `selenium` | ≥ 4.15.0 |

### Verificare dependențe (SSH / Terminal add-on)

Conectează-te la HA (add-on **Terminal & SSH** sau SSH pe portul configurat):

```bash
# Binar browser — ambele integrări
which chromium || which chromium-browser
which chromedriver

# Doar Hidroelectrica (energie electrică)
which Xvfb
Xvfb -help 2>&1 | head -1

# Test rapid DISPLAY (Hidro)
export DISPLAY=:99
Xvfb :99 -screen 0 1280x720x24 &
echo "DISPLAY=$DISPLAY"
```

**Rezultat așteptat pe HA OS recent:**

```
/usr/bin/chromium
/usr/bin/chromedriver
/usr/bin/Xvfb
```

### Dacă lipsește Chromium / Xvfb

Pe **Home Assistant OS**, binarele sunt de obicei preinstalate. Dacă lipsesc:

1. Actualizează HA OS la ultima versiune
2. Add-on **Terminal & SSH** → acces root
3. Pe unele instalări vechi, poți instala via:

```bash
# Doar dacă which chromium / which Xvfb returnează gol — HA OS folosește Alpine/apk
apk update
apk add chromium chromium-chromedriver xvfb
```

> Nu modifica Python-ul sistem al Home Assistant manual (`pip install` în containerul core).

### Variabile de mediu opționale

| Variabilă | Implicit | Descriere |
|-----------|----------|-----------|
| `CHROMIUM_PATH` | `/usr/bin/chromium` | Cale browser |
| `CHROMEDRIVER_PATH` | `/usr/bin/chromedriver` | Cale driver Selenium |
| `HIDROELECTRICA_DIR` | `/config/hidroelectrica` | Override folder date Hidro |

### Lock Chromium partajat

Premier și Hidro **partajează** același lock (`/config/.chromium_automation.lock`) ca să nu pornească două browsere simultan. Dacă un refresh durează >3 min, celălalt așteaptă — comportament normal.

---

## 2. Instalare integrări

### Metoda A — HACS (recomandat)

1. Instalează [HACS](https://hacs.xyz/docs/setup/download) dacă nu îl ai
2. **HACS** → **Integrations** → **⋮** (meniu) → **Custom repositories**
3. Adaugă:
   - **Repository:** `https://github.com/SmartEnergyHub/hidro-premierenergy`
   - **Category:** Integration
4. **Download** repository
5. **Restart Home Assistant** (Setări → Sistem → Restart)
6. **Setări** → **Dispozitive și servicii** → **Adaugă integrare**

### Metoda B — Manual (fără HACS)

```bash
cd /config
git clone --depth 1 https://github.com/SmartEnergyHub/hidro-premierenergy.git /tmp/ha-energie
cp -r /tmp/ha-energie/custom_components/premier_energy custom_components/
cp -r /tmp/ha-energie/custom_components/hidroelectrica custom_components/
rm -rf /tmp/ha-energie
```

Apoi **Restart Home Assistant**.

---

## 3. Configurare Premier Energy (gaze naturale)

### Pas 1 — Adaugă integrarea

1. **Setări** → **Dispozitive și servicii** → **Adaugă integrare**
2. Caută: **Premier Energy**
3. Introdu:
   - **Email** — contul de la [my.premierenergy.ro](https://my.premierenergy.ro)
   - **Parolă**
4. Confirmă — integrarea face login Azure B2C automat (1–2 min prima dată)

### Pas 2 — Verifică entitățile

După configurare apare dispozitivul **Premier Energy** cu:

| Entitate (tipic) | Descriere |
|------------------|-----------|
| `sensor.*_factura_suma` | Suma ultima factură (RON) |
| `sensor.*_factura_numar` | Număr factură |
| `sensor.*_scadenta` | Data scadenței |
| `sensor.*_consum_m3` | Consum gaze (m³) |
| `sensor.*_consum_mwh` | Consum (MWh) |
| `sensor.*_adresa` | Adresa locului de consum |
| `binary_sensor.*_conectat` | Token JWT valid |
| `button.*_reinprospateaza_sesiunea` | Refresh manual |
| `button.*_re_login_fortat` | Re-login Azure B2C |

> **Important:** ID-urile exacte depind de numele dispozitivului. Verifică în **Instrumente pentru dezvoltatori** → **Stări** → filtrează `premier_energy`.

### Pas 3 — Comportament automat

- Refresh token + date: la fiecare **10 minute**
- Re-login automat când tokenul expiră (<20 min margin)
- Stocare locală: `/config/premier_energy/<entry_id>/`

### Pas 4 — Card Lovelace

Vezi [examples/lovelace_premier_energy.yaml](../examples/lovelace_premier_energy.yaml).

---

## 4. Configurare Hidroelectrica (energie electrică)

### Pas 1 — Adaugă integrarea

1. **Setări** → **Dispozitive și servicii** → **Adaugă integrare**
2. Caută: **Hidroelectrica**
3. Introdu:
   - **Utilizator** — cont ihidro.ro
   - **Parolă**
   - **Telegram bot token** (opțional) — pentru notificări legacy
   - **Telegram chat ID** (opțional)
4. Prima autentificare poate dura **2–4 min** (Xvfb + reCAPTCHA)

### Pas 2 — Verifică entitățile

| Entitate (tipic) | Descriere |
|------------------|-----------|
| `sensor.*_factura_suma` | Suma ultima factură (RON) |
| `sensor.*_factura_numar` | Număr factură |
| `sensor.*_scadenta` | Scadență (dd/mm/yyyy) |
| `sensor.*_pod` | Cod POD |
| `sensor.*_sold` | Sold cont (RON) |
| `sensor.*_index_curent` | Index contor (kWh) |
| `sensor.*_consum_mediu` | Consum mediu lunar (RON) |
| `binary_sensor.*_sesiune_ok` | Sesiune portal validă |
| `binary_sensor.*_perioada_autocitire` | Autocitire activă |
| `button.*_reinprospateaza_sesiunea` | Refresh + fetch date |
| `button.*_re_login_fortat` | Auto-login Xvfb |

> Filtrează `hidroelectrica` în **Stări** pentru ID-uri exacte.

### Pas 3 — Comportament automat

- Keepalive + fetch date: la fiecare **5 minute**
- Auto-login Xvfb dacă sesiunea expiră
- Scrie și `data.json` în `/config/hidroelectrica/` (compatibil carduri legacy)
- Stocare sesiune: `/config/hidroelectrica/<entry_id>/`

### Pas 4 — Card Lovelace

Vezi [examples/lovelace_hidroelectrica.yaml](../examples/lovelace_hidroelectrica.yaml).

---

## 5. Migrare de la setup legacy (shell_command)

Dacă ai deja scripturi în `/config/premier_energy/` sau `/config/hidroelectrica/`:

1. Instalează integrările HACS (pașii de mai sus)
2. Testează 24–48 h
3. **Dezactivează** automatizările YAML duplicate (evită dublu polling + lock Chromium):

```yaml
# packages/energie/premier_token_refresh.yaml — comentează sau șterge:
# - id: premier_refresh_token_schedule
# - id: premier_health_watchdog

# packages/energie/hidroelectrica.yaml — comentează sau șterge:
# - id: hidro_session_manager_schedule
# - id: hidro_refresh_schedule
```

4. Păstrează scripturile Telegram din `automations.yaml` — pot apela serviciile noi:

```yaml
action: premier_energy.download_invoice
data:
  invoice_number: "001111468965"
```

Detalii: [MIGRATION.md](MIGRATION.md)

---

## 6. Servicii disponibile

| Serviciu | Integrare | Descriere |
|----------|-----------|-----------|
| `premier_energy.refresh_session` | Gaze naturale | Refresh JWT + date |
| `premier_energy.force_login` | Gaze naturale | Re-login Azure B2C |
| `premier_energy.download_invoice` | Gaze naturale | PDF factură |
| `premier_energy.export_debug` | Gaze naturale | Debug în log (fără secrete) |
| `hidroelectrica.refresh_session` | Energie electrică | Keepalive + fetch |
| `hidroelectrica.force_login` | Energie electrică | Auto-login Xvfb |
| `hidroelectrica.download_invoice` | Energie electrică | PDF factură |
| `hidroelectrica.export_debug` | Energie electrică | Debug în log |

Exemple YAML: [examples/services.yaml](../examples/services.yaml)

---

## 7. Depanare rapidă

| Simptom | Premier Energy (gaze) | Hidroelectrica (electric) |
|---------|----------------------|---------------------------|
| `invalid_auth` | Verifică email/parolă pe portal | Verifică user/parolă pe ihidro.ro |
| Date vechi | Apasă **Reîmprospătează sesiunea** | La fel |
| Browser blocat | Așteaptă 3 min (lock) | La fel |
| reCAPTCHA fail | — | Verifică `which Xvfb` |
| Chromium lipsă | `which chromium` | La fel |

Ghid complet: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 8. Securitate

- Credențialele sunt stocate criptat în **Config Entries** HA
- Nu comite `secrets.json`, `token.txt`, `session.json` în git
- Diagnostics (Integrări → ⋮ → Download diagnostics) maschează parolele

Vezi [SECURITY.md](SECURITY.md)
