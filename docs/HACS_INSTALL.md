# Instalare via HACS — test complet

Repository: **https://github.com/SmartEnergyHub/hidro-premierenergy**

Integrări incluse:

| Domain | Nume | Versiune (main) |
|--------|------|-----------------|
| `premier_energy` | Premier Energy (gaze naturale) | manifest.json |
| `hidroelectrica` | Hidroelectrica (energie electrică) | manifest.json |

---

## 1. Adaugă repository custom în HACS

1. **HACS** → **Integrations** → meniu ⋮ → **Custom repositories**
2. **Repository:** `https://github.com/SmartEnergyHub/hidro-premierenergy`
3. **Category:** Integration
4. **Add**

## 2. Instalează integrările

1. **HACS** → **Integrations** → **Explore & Download Repositories**
2. Caută **Smart Energy Hub** sau **HA Energie**
3. Instalează — HACS copiază ambele foldere din `custom_components/`
4. **Restart Home Assistant** (sau Reload integrări noi)

## 3. Configurare

**Setări → Dispozitive și servicii → Adaugă integrare**

- **Premier Energy (gaze naturale)** — email + parolă [my.premierenergy.ro](https://my.premierenergy.ro)
- **Hidroelectrica (energie electrică)** — user + parolă [ihidro.ro](https://ihidro.ro/portal/)

Dependențe pe HA OS: `chromium`, `chromedriver`, `Xvfb` (Hidro).

## 4. Verificare instalare reușită

```text
/config/custom_components/premier_energy/manifest.json   → version
/config/custom_components/hidroelectrica/manifest.json  → version
```

Butoane: **Reîmprospătează sesiunea**, **Re-login forțat**, **Support Development**.

Servicii: `premier_energy.refresh_session`, `hidroelectrica.force_login`, etc.

## 5. Dezactivează legacy (dacă migrezi)

Dacă ai `/config/packages/energie/hidroelectrica.yaml` sau scripturi în `/config/hidroelectrica/*.py` cu `shell_command`, **dezactivează**-le — integrarea HACS le înlocuiește.

## 6. Update HACS

La fiecare release: HACS → integrare → **Update** → Restart HA.

Release-uri: https://github.com/SmartEnergyHub/hidro-premierenergy/releases
