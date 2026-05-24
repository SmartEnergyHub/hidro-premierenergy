# Pagină Donate — deploy pe server (NU comite redirect PayPal în git)

## URL public (folosit în repo, README, HACS, HA)
`https://hidro-premierenergy.ro/donate`

Repository-ul conține **doar** acest URL. Destinația finală de plată se configurează **exclusiv pe server**.

## Deploy pe server web

1. Creează un landing page elegant la `/donate/index.html`
2. Configurează redirect server-side (nginx `return 302` către destinația PayPal) **în config nginx**, nu în git
3. Exemplu nginx:

```nginx
location = /donate {
    return 302 https://DESTINATIA_TA_CONFIGURATA_PE_SERVER;
}
```

Sau PHP cu variabilă de mediu `DONATE_REDIRECT_URL` din `.env` server (gitignored).

4. Verifică: `curl -I https://hidro-premierenergy.ro/donate`

## Home Assistant / GitHub
Toate link-urile „Support Development” folosesc: **https://hidro-premierenergy.ro/donate**
