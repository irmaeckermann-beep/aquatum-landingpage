# Aquatum Lead-Proxy

Kleiner Python-stdlib-Dienst (keine Dependencies), der die Formular-Submits der
Landingpage entgegennimmt, den Kontakt in **Brevo** anlegt und dem Lead seine
Wasser-Auswertung per E-Mail schickt. Der Brevo-API-Key bleibt server-seitig.

Frontend postet an `/api/lead` (siehe `BREVO_ENDPOINT` in `../script.js`),
nginx leitet `/api/lead` auf `127.0.0.1:3010`.

## Setup auf dem Server (einmalig)

```bash
# 1. .env AUSSERHALB des Web-Roots anlegen (sonst via https://.../.env abrufbar!)
cp /opt/aquatum-landingpage/server/.env.example /etc/aquatum-leadproxy.env
nano /etc/aquatum-leadproxy.env             # echten Key eintragen
chown root:root /etc/aquatum-leadproxy.env
chmod 600 /etc/aquatum-leadproxy.env

# 2. systemd-Service installieren
cp /opt/aquatum-landingpage/server/aquatum-leadproxy.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now aquatum-leadproxy

# 3. nginx vhost: location = /api/lead -> 127.0.0.1:3010 ergaenzen.
#    WICHTIG zusaetzlich (Web-Root = Repo-Ordner!): Dotfiles + server/ sperren:
#      location ~ /\.       { deny all; return 404; }
#      location ^~ /server/ { deny all; return 404; }
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
