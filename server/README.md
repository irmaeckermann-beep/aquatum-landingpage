# Aquatum Lead-Proxy

Kleiner Python-stdlib-Dienst (keine Dependencies), der die Formular-Submits der
Landingpage entgegennimmt, den Kontakt in **Brevo** anlegt und dem Lead seine
Wasser-Auswertung per E-Mail schickt. Der Brevo-API-Key bleibt server-seitig.

Frontend postet an `/api/lead` (siehe `BREVO_ENDPOINT` in `../script.js`),
nginx leitet `/api/lead` auf `127.0.0.1:3010`.

## Setup auf dem Server (einmalig)

```bash
# 1. .env anlegen (NICHT im Repo)
cp /opt/aquatum-landingpage/server/.env.example /opt/aquatum-landingpage/.env
nano /opt/aquatum-landingpage/.env          # echten Key eintragen
chown www-data:www-data /opt/aquatum-landingpage/.env
chmod 600 /opt/aquatum-landingpage/.env

# 2. systemd-Service installieren
cp /opt/aquatum-landingpage/server/aquatum-leadproxy.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now aquatum-leadproxy

# 3. nginx: location /api/lead -> 127.0.0.1:3010 (im vhost ergaenzen), dann
nginx -t && systemctl reload nginx
```

## Updates

```bash
cd /opt/aquatum-landingpage && git pull
systemctl restart aquatum-leadproxy
```

## Logs

```bash
journalctl -u aquatum-leadproxy -f
```
