# Auto-Deploy

Pushes auf den `main`-Branch dieses Repos gehen **automatisch live** auf
`https://www.wasserfilter-beratung.ch` (Server 2).

- Ein Cron-Job auf dem Server prüft alle ~2 Minuten auf neue Commits und
  zieht sie per `git pull --ff-only` + Neustart des Lead-Proxys live
  (`/usr/local/bin/deploy-aquatum`).
- Kein manueller Schritt nötig: einfach auf `main` pushen.
- Geht nur vorwärts (Fast-Forward) – die Live-Site wird nie überschrieben oder
  zurückgerollt. Server-Geheimnisse (`/etc/aquatum-leadproxy.env`) und die
  gespeicherten Leads (`/var/lib/aquatum-leadproxy/leads.jsonl`) bleiben unberührt.
- Deploy-Protokoll: `/var/log/deploy.log` auf dem Server.
