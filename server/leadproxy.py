#!/usr/bin/env python3
"""Aquatum Lead-Proxy: nimmt Formular-Submits der Landingpage entgegen,
legt den Kontakt in Brevo an und schickt dem Lead seine Wasser-Auswertung.

Der Brevo-API-Key bleibt server-seitig (EnvironmentFile), nie im Frontend.
Laeuft hinter nginx (location /api/lead -> 127.0.0.1:PORT)."""

import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Server 2 ist bei Brevo nur ueber IPv4 (204.168.145.158) gewhitelistet.
# IPv6 wuerde 401 liefern -> getaddrinfo auf IPv4 zwingen.
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(host, *args, **kwargs):
    return [r for r in _orig_getaddrinfo(host, *args, **kwargs) if r[0] == socket.AF_INET]
socket.getaddrinfo = _ipv4_only

HOST = os.environ.get("LEADPROXY_HOST", "127.0.0.1")
PORT = int(os.environ.get("LEADPROXY_PORT", "3010"))
API_KEY = os.environ.get("BREVO_API_KEY", "")
LIST_ID = int(os.environ.get("BREVO_LIST_ID", "0") or "0")
SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "")
SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Aquatum")
NOTIFY_EMAIL = os.environ.get("LEAD_NOTIFY_EMAIL", "")
BREVO_API = "https://api.brevo.com/v3"
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

TEXT_ATTRS = ["TELEFON", "PLZ_ORT", "NACHRICHT", "REGION", "PAKET", "OPT_IN"]
NUM_ATTRS = ["SCORE", "HAERTE", "KOSTEN"]


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def brevo(method, path, payload):
    req = urllib.request.Request(
        BREVO_API + path,
        data=json.dumps(payload).encode("utf-8"),
        method=method,
        headers={"api-key": API_KEY, "content-type": "application/json",
                 "accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def upsert_contact(f):
    attrs = {}
    if f.get("FIRSTNAME"):
        attrs["VORNAME"] = f["FIRSTNAME"]
    if f.get("LASTNAME"):
        attrs["NACHNAME"] = f["LASTNAME"]
    for k in TEXT_ATTRS:
        if f.get(k):
            attrs[k] = f[k]
    for k in NUM_ATTRS:
        v = f.get(k, "").strip()
        if v:
            try:
                attrs[k] = float(v)
            except ValueError:
                pass
    payload = {"email": f["EMAIL"], "updateEnabled": True, "attributes": attrs}
    if LIST_ID:
        payload["listIds"] = [LIST_ID]
    return brevo("POST", "/contacts", payload)


def send_eval_mail(f):
    if not SENDER_EMAIL:
        return None, "no sender configured"
    name = (f.get("FIRSTNAME", "") + " " + f.get("LASTNAME", "")).strip()
    score = f.get("SCORE", "?")
    haerte = f.get("HAERTE", "?")
    kosten = f.get("KOSTEN", "?")
    region = f.get("REGION", "")
    html = f"""<!DOCTYPE html><html lang="de"><body style="font-family:Arial,Helvetica,sans-serif;color:#1a2b3c;line-height:1.6;margin:0;padding:24px;background:#f4f8fb">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;padding:32px">
<h1 style="font-size:22px;margin:0 0 8px">Ihre persönliche Wasser-Auswertung</h1>
<p>Guten Tag{(' ' + f.get('FIRSTNAME','')) if f.get('FIRSTNAME') else ''},</p>
<p>vielen Dank für Ihren Wasser-Check. Hier Ihr Ergebnis auf einen Blick:</p>
<table style="width:100%;border-collapse:collapse;margin:16px 0">
<tr><td style="padding:8px 0;border-bottom:1px solid #e3edf3">Wasser-Score</td><td style="padding:8px 0;border-bottom:1px solid #e3edf3;text-align:right;font-weight:700">{score}/100</td></tr>
<tr><td style="padding:8px 0;border-bottom:1px solid #e3edf3">Wasserhärte</td><td style="padding:8px 0;border-bottom:1px solid #e3edf3;text-align:right;font-weight:700">ca. {haerte} °fH</td></tr>
<tr><td style="padding:8px 0;border-bottom:1px solid #e3edf3">Geschätzte Folgekosten</td><td style="padding:8px 0;border-bottom:1px solid #e3edf3;text-align:right;font-weight:700">CHF {kosten}/Jahr</td></tr>
{f'<tr><td style="padding:8px 0">Region</td><td style="padding:8px 0;text-align:right;font-weight:700">{region}</td></tr>' if region else ''}
</table>
<p>Ein Experte von Aquatum meldet sich für Ihre <strong>kostenlose Detail-Analyse vor Ort</strong>. So erfahren Sie genau, welche Aufbereitung sich für Ihr Wasser lohnt.</p>
<p>Herzliche Grüsse<br>Ihr Aquatum-Team</p>
<p style="font-size:12px;color:#7488a0;margin-top:24px">Aquatum · Wasserfilter-Beratung Schweiz · +41 61 851 00 89</p>
</div></body></html>"""
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": f["EMAIL"], "name": name or f["EMAIL"]}],
        "subject": "Ihre persönliche Wasser-Auswertung",
        "htmlContent": html,
    }
    return brevo("POST", "/smtp/email", payload)


def send_notify_mail(f):
    """Interne Benachrichtigung an das Aquatum-/Leadhunter-Team bei jedem Lead."""
    if not SENDER_EMAIL or not NOTIFY_EMAIL:
        return None, "no notify recipient configured"
    name = (f.get("FIRSTNAME", "") + " " + f.get("LASTNAME", "")).strip() or "—"
    fields = [
        ("Name", name),
        ("E-Mail", f.get("EMAIL", "")),
        ("Telefon", f.get("TELEFON", "")),
        ("PLZ / Ort", f.get("PLZ_ORT", "")),
        ("Region", f.get("REGION", "")),
        ("Wasser-Score", f"{f.get('SCORE', '')}/100" if f.get("SCORE") else ""),
        ("Wasserhärte", f"ca. {f.get('HAERTE', '')} °fH" if f.get("HAERTE") else ""),
        ("Folgekosten", f"CHF {f.get('KOSTEN', '')}/Jahr" if f.get("KOSTEN") else ""),
        ("Paket", f.get("PAKET", "")),
        ("Opt-In", f.get("OPT_IN", "")),
        ("Nachricht", f.get("NACHRICHT", "")),
    ]
    rows = "".join(
        f'<tr><td style="padding:6px 12px 6px 0;color:#7488a0;white-space:nowrap;vertical-align:top">{label}</td>'
        f'<td style="padding:6px 0;font-weight:600">{value}</td></tr>'
        for label, value in fields if value
    )
    html = f"""<!DOCTYPE html><html lang="de"><body style="font-family:Arial,Helvetica,sans-serif;color:#1a2b3c;line-height:1.5;margin:0;padding:24px;background:#f4f8fb">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;padding:28px">
<h1 style="font-size:20px;margin:0 0 4px">Neuer Lead · Wasserfilter-Beratung</h1>
<p style="margin:0 0 16px;color:#7488a0">{name} · Score {f.get('SCORE', '?')}/100</p>
<table style="width:100%;border-collapse:collapse;font-size:14px">{rows}</table>
<p style="font-size:12px;color:#7488a0;margin-top:20px">Automatische Benachrichtigung von wasserfilter-beratung.ch · Antwort geht direkt an den Lead.</p>
</div></body></html>"""
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": NOTIFY_EMAIL}],
        "replyTo": {"email": f["EMAIL"], "name": name if name != "—" else f["EMAIL"]},
        "subject": f"Neuer Lead · {name} · Score {f.get('SCORE', '?')}",
        "htmlContent": html,
    }
    return brevo("POST", "/smtp/email", payload)


class Handler(BaseHTTPRequestHandler):
    server_version = "aquatum-leadproxy"

    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204)

    def do_GET(self):
        # Health check
        self._send(200, b'{"ok":true,"service":"aquatum-leadproxy"}')

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        f = {k: v[0] for k, v in urllib.parse.parse_qs(raw, keep_blank_values=True).items()}

        # Honeypot -> Bot, still erfolgreich quittieren
        if f.get("email_address_check", "").strip():
            return self._send(200, b'{"ok":true}')

        email = f.get("EMAIL", "").strip()
        if not email or not EMAIL_RE.match(email):
            return self._send(400, b'{"ok":false,"error":"invalid_email"}')
        f["EMAIL"] = email

        status, resp = upsert_contact(f)
        if status not in (200, 201, 204):
            log(f"[lead] contact FAIL {status}: {resp[:300]}")
            return self._send(502, b'{"ok":false,"error":"crm"}')
        log(f"[lead] contact OK {status} <{email}> score={f.get('SCORE','')}")

        mstatus, mresp = send_eval_mail(f)
        if mstatus in (200, 201):
            log(f"[lead] mail OK <{email}>")
        else:
            log(f"[lead] mail SKIP/FAIL {mstatus}: {str(mresp)[:200]}")

        nstatus, nresp = send_notify_mail(f)
        if nstatus in (200, 201):
            log(f"[lead] notify OK <{NOTIFY_EMAIL}>")
        elif nstatus is not None:
            log(f"[lead] notify FAIL {nstatus}: {str(nresp)[:200]}")

        self._send(200, b'{"ok":true}')

    def log_message(self, *a):
        pass  # eigenes Logging via log()


def main():
    if not API_KEY:
        log("FATAL: BREVO_API_KEY fehlt"); sys.exit(1)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    log(f"aquatum-leadproxy listening on {HOST}:{PORT} (list={LIST_ID}, sender={SENDER_EMAIL or 'none'}, notify={NOTIFY_EMAIL or 'none'})")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
