# HA Energie România

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/johnny29/hidro-premierenergy)](https://github.com/johnny29/hidro-premierenergy/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Integrări custom Home Assistant pentru portalurile românești de utilități — **FULL AUTO**, gata de producție.

| Integrare | Furnizor | Tip | Portal |
|-----------|----------|-----|--------|
| **Premier Energy** | Premier Energy | **Gaze naturale** | [my.premierenergy.ro](https://my.premierenergy.ro) |
| **Hidroelectrica** | Hidroelectrica | **Energie electrică** | [ihidro.ro/portal](https://ihidro.ro/portal/) |

> Introdu **email/parolă** sau **user/parolă** o singură dată în UI. Fără cookies manuale, token F12 sau YAML pentru credențiale.

---

## Documentație

| Document | Conținut |
|----------|----------|
| **[docs/INSTALLATION.md](docs/INSTALLATION.md)** | **Ghid complet instalare** — dependențe, pași, verificări SSH |
| [docs/MIGRATION.md](docs/MIGRATION.md) | Migrare de la shell_command / scripturi legacy |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Depanare |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arhitectură tehnică |

---

## Dependențe (rezumat)

| Dependență | Premier Energy (gaze naturale) | Hidroelectrica (energie electrică) |
|------------|:------------------------------:|:----------------------------------:|
| Home Assistant ≥ 2024.12 | ✅ | ✅ |
| HACS ≥ 1.34 (opțional) | ✅ | ✅ |
| Chromium + ChromeDriver | ✅ | ✅ |
| Xvfb (display virtual) | — | ✅ obligatoriu |
| Python: `requests`, `selenium` | auto (manifest) | auto (manifest) |

Verificare rapidă pe HA OS (SSH):

```bash
which chromium chromedriver Xvfb
```

Detalii complete, variabile de mediu, instalare pe Docker/Core: **[docs/INSTALLATION.md](docs/INSTALLATION.md)**

---

## Instalare rapidă

### HACS

1. **HACS** → **Integrations** → **Custom repositories** → `https://github.com/johnny29/hidro-premierenergy`
2. **Download** → **Restart HA**
3. **Setări** → **Dispozitive și servicii** → **Adaugă integrare**
4. Caută **Premier Energy** (gaze naturale) sau **Hidroelectrica** (energie electrică)

### Manual

```bash
cd /config
git clone --depth 1 https://github.com/johnny29/hidro-premierenergy.git /tmp/ha-energie
cp -r /tmp/ha-energie/custom_components/premier_energy custom_components/
cp -r /tmp/ha-energie/custom_components/hidroelectrica custom_components/
# Restart Home Assistant
```

---

## Configurare

### Premier Energy (gaze naturale)

1. Adaugă integrarea → email + parolă [my.premierenergy.ro](https://my.premierenergy.ro)
2. Refresh automat token JWT la **10 minute**
3. Entități: factură, scadență, consum m³/MWh, adresă, conectivitate

### Hidroelectrica (energie electrică)

1. Adaugă integrarea → user + parolă [ihidro.ro](https://ihidro.ro/portal/)
2. Opțional: Telegram bot token + chat ID
3. Refresh sesiune + date la **5 minute**; auto-login Xvfb pentru reCAPTCHA
4. Entități: factură, POD, sold, index kWh, autocitire, conectivitate

---

## Carduri Lovelace

| Fișier | Descriere |
|--------|-----------|
| [examples/lovelace_premier_energy.yaml](examples/lovelace_premier_energy.yaml) | Card complet **gaze naturale** |
| [examples/lovelace_hidroelectrica.yaml](examples/lovelace_hidroelectrica.yaml) | Card complet **energie electrică** |
| [examples/dashboard_energie.yaml](examples/dashboard_energie.yaml) | Dashboard combinat |

> După instalare, verifică ID-urile entităților în **Instrumente pentru dezvoltatori → Stări** și adaptează YAML-ul.

```
┌─────────────────────────────────────┐
│ Premier Energy (gaze naturale)      │
│  Factură: 330.92 RON  │  Scadență  │
│  Consum: 125 m³       │  ● Conectat│
│  [ Reîmprospătează ] [ Re-login ]    │
├─────────────────────────────────────┤
│ Hidroelectrica (energie electrică)  │
│  Factură: 887.2 RON   │  POD: …    │
│  Index: 4521 kWh      │  ● Sesiune │
│  ⚡ Autocitire activă               │
│  [ Reîmprospătează ] [ Re-login ]   │
└─────────────────────────────────────┘
```

---

## Funcționalități

### Ambele integrări
- Config Flow UI (fără editare YAML pentru credențiale)
- Auto-login și auto-refresh
- Self-healing, retry, watchdog
- Recovery după restart HA
- Diagnostics (secrete mascate)
- Servicii: refresh, force login, PDF, debug export

### Premier Energy (gaze naturale)
- Sumă / număr factură, scadență
- Consum m³ și MWh
- Adresă loc de consum
- JWT refresh la 10 min (Azure B2C)

### Hidroelectrica (energie electrică)
- Factură, POD, sold, index contor
- Senzor perioadă autocitire
- Keepalive sesiune la 5 min
- Xvfb + Chromium headed (reCAPTCHA)

---

## Servicii

| Serviciu | Integrare |
|----------|-----------|
| `premier_energy.refresh_session` | Gaze naturale |
| `premier_energy.force_login` | Gaze naturale |
| `premier_energy.download_invoice` | Gaze naturale |
| `hidroelectrica.refresh_session` | Energie electrică |
| `hidroelectrica.force_login` | Energie electrică |
| `hidroelectrica.download_invoice` | Energie electrică |

Exemple: [examples/services.yaml](examples/services.yaml)

---

## Compatibilitate

| Platformă | Suport |
|-----------|--------|
| Home Assistant OS | ✅ Recomandat |
| Supervised | ✅ |
| Container | ⚠️ Chromium + Xvfb manual |
| Core (venv) | ⚠️ Setup browser manual |
| Raspberry Pi ARM64 | ✅ |
| x86-64 | ✅ |

---

## Migrare legacy

Scripturile din `/config/premier_energy/` și `/config/hidroelectrica/` **nu se șterg** automat. Dezactivează automatizările YAML duplicate după testare.

[docs/MIGRATION.md](docs/MIGRATION.md)

---

## Securitate

- Credențiale criptate în Config Entries HA
- Fără secrete în repository
- [SECURITY.md](SECURITY.md)

---

## Licență

[MIT](LICENSE) © HA Energie România Contributors
