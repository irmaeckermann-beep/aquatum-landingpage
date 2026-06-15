#!/usr/bin/env python3
"""Aquatum Lead-Proxy: nimmt Formular-Submits der Landingpage entgegen,
legt den Kontakt in Brevo an und schickt dem Lead seine Wasser-Auswertung.

Der Brevo-API-Key bleibt server-seitig (EnvironmentFile), nie im Frontend.
Laeuft hinter nginx (location /api/lead -> 127.0.0.1:PORT)."""

import hashlib
import hmac
import json
import os
import re
import socket
import sys
import threading
import time
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
# Feste zusätzliche Empfänger der Lead-Benachrichtigung (immer mit dabei).
EXTRA_NOTIFY = ["info@regenfaenger.ch"]


def notify_recipients():
    """Empfängerliste für die Lead-Benachrichtigung: LEAD_NOTIFY_EMAIL (auch
    mehrere, durch Komma/Semikolon getrennt) plus die festen EXTRA_NOTIFY,
    dedupliziert und ohne Leereinträge."""
    raw = re.split(r"[,;\s]+", NOTIFY_EMAIL or "")
    seen, out = set(), []
    for e in [x.strip() for x in raw] + EXTRA_NOTIFY:
        k = e.lower()
        if e and EMAIL_RE.match(e) and k not in seen:
            seen.add(k)
            out.append(e)
    return out


BREVO_API = "https://api.brevo.com/v3"
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Facebook/Meta Conversions API (server-seitig). Token NUR aus EnvironmentFile,
# nie im Repo/Frontend. Feuert ausschliesslich bei erteilter Einwilligung.
META_PIXEL_ID = os.environ.get("META_PIXEL_ID", "")
META_CAPI_TOKEN = os.environ.get("META_CAPI_TOKEN", "")
META_GRAPH_VERSION = os.environ.get("META_GRAPH_VERSION", "v21.0")
META_TEST_EVENT_CODE = os.environ.get("META_TEST_EVENT_CODE", "")
GRAPH_API = "https://graph.facebook.com"

TEXT_ATTRS = ["TELEFON", "PLZ_ORT", "NACHRICHT", "REGION", "PAKET", "OPT_IN"]
NUM_ATTRS = ["SCORE", "HAERTE", "KOSTEN"]

# Lead-Backend: jeder Lead wird zusaetzlich lokal als JSON-Zeile gespeichert,
# damit das Team die Leads im geschuetzten Admin-Bereich (/api/leads) ansehen kann.
# Datei MUSS ausserhalb des Web-Roots liegen (sonst oeffentlich abrufbar!).
LEADS_FILE = os.environ.get("LEADS_FILE", "/var/lib/aquatum-leadproxy/leads.jsonl")
# Passwort/Token fuer den Admin-Zugriff auf /api/leads. Leer = Endpoint deaktiviert.
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
_leads_lock = threading.Lock()


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def store_lead(f, client_ip):
    """Haengt den Lead als JSON-Zeile an LEADS_FILE an (Quelle fuer das Admin-Backend)."""
    if not LEADS_FILE:
        return
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "produkt": f.get("PRODUKT", ""),
        "vorname": f.get("FIRSTNAME", ""),
        "nachname": f.get("LASTNAME", ""),
        "email": f.get("EMAIL", ""),
        "telefon": f.get("TELEFON", ""),
        "plz_ort": f.get("PLZ_ORT", ""),
        "region": f.get("REGION", ""),
        "score": f.get("SCORE", ""),
        "haerte": f.get("HAERTE", ""),
        "kosten": f.get("KOSTEN", ""),
        "paket": f.get("PAKET", ""),
        "nachricht": f.get("NACHRICHT", ""),
        "opt_in": f.get("OPT_IN", ""),
        "ip": client_ip,
    }
    try:
        with _leads_lock:
            d = os.path.dirname(LEADS_FILE)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(LEADS_FILE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        log(f"[lead] store FAIL: {e}")


def read_leads(limit=10000):
    """Liest gespeicherte Leads (neueste zuerst)."""
    try:
        with _leads_lock:
            with open(LEADS_FILE, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
    except FileNotFoundError:
        return []
    except Exception as e:  # noqa: BLE001
        log(f"[lead] read FAIL: {e}")
        return []
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:  # noqa: BLE001
            pass
    out.reverse()
    return out


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


def _hash(value):
    """SHA-256 der normalisierten (lowercase, getrimmten) Angabe – Meta-Vorgabe."""
    return hashlib.sha256((value or "").strip().lower().encode("utf-8")).hexdigest()


def _norm_phone(value):
    """Telefonnummer auf Ziffern reduzieren, Schweizer Vorwahl ergaenzen."""
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return ""
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = "41" + digits[1:]
    return digits


def graph_post(path, payload):
    req = urllib.request.Request(
        GRAPH_API + path,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def send_capi_lead(f, client_ip, client_ua):
    """Server-seitiges 'Lead'-Event an die Meta Conversions API.
    Nur bei erteilter Pixel-Einwilligung (FB_CONSENT=1) und konfiguriertem Token.
    event_id ist identisch zum Browser-Pixel-Event -> Meta dedupliziert."""
    if not META_PIXEL_ID or not META_CAPI_TOKEN:
        return None, "capi not configured"
    if f.get("FB_CONSENT", "") != "1":
        return None, "no consent"
    user_data = {}
    if f.get("EMAIL"):
        user_data["em"] = [_hash(f["EMAIL"])]
    ph = _norm_phone(f.get("TELEFON", ""))
    if ph:
        user_data["ph"] = [_hash(ph)]
    if f.get("FIRSTNAME"):
        user_data["fn"] = [_hash(f["FIRSTNAME"])]
    if f.get("LASTNAME"):
        user_data["ln"] = [_hash(f["LASTNAME"])]
    # fbp/fbc werden UNGEHASHT uebermittelt (Meta-Vorgabe)
    if f.get("FBP"):
        user_data["fbp"] = f["FBP"]
    if f.get("FBC"):
        user_data["fbc"] = f["FBC"]
    if client_ip:
        user_data["client_ip_address"] = client_ip
    if client_ua:
        user_data["client_user_agent"] = client_ua
    event = {
        "event_name": "Lead",
        "event_time": int(time.time()),
        "action_source": "website",
        "user_data": user_data,
    }
    if f.get("EVENT_ID"):
        event["event_id"] = f["EVENT_ID"]
    if f.get("EVENT_SOURCE_URL"):
        event["event_source_url"] = f["EVENT_SOURCE_URL"]
    payload = {"data": [event], "access_token": META_CAPI_TOKEN}
    if META_TEST_EVENT_CODE:
        payload["test_event_code"] = META_TEST_EVENT_CODE
    return graph_post(f"/{META_GRAPH_VERSION}/{META_PIXEL_ID}/events", payload)


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
<h1 style="font-size:22px;margin:0 0 8px">Ihr persönlicher Wasserrapport</h1>
<p>Guten Tag{(' ' + f.get('FIRSTNAME','')) if f.get('FIRSTNAME') else ''},</p>
<p>vielen Dank für Ihre Anfrage. Hier Ihr Wasserrapport auf einen Blick:</p>
<table style="width:100%;border-collapse:collapse;margin:16px 0">
<tr><td style="padding:8px 0;border-bottom:1px solid #e3edf3">Wasser-Score</td><td style="padding:8px 0;border-bottom:1px solid #e3edf3;text-align:right;font-weight:700">{score}/100</td></tr>
<tr><td style="padding:8px 0;border-bottom:1px solid #e3edf3">Wasserhärte</td><td style="padding:8px 0;border-bottom:1px solid #e3edf3;text-align:right;font-weight:700">ca. {haerte} °fH</td></tr>
<tr><td style="padding:8px 0;border-bottom:1px solid #e3edf3">Geschätzte Folgekosten</td><td style="padding:8px 0;border-bottom:1px solid #e3edf3;text-align:right;font-weight:700">CHF {kosten}/Jahr</td></tr>
{f'<tr><td style="padding:8px 0">Region</td><td style="padding:8px 0;text-align:right;font-weight:700">{region}</td></tr>' if region else ''}
</table>
<p>Ein Experte von Aquatum meldet sich für Ihre <strong>kostenlose Beratung vor Ort</strong>. So erfahren Sie genau, welche Wasseraufbereitung sich für Sie lohnt.</p>
<p>Herzliche Grüsse<br>Ihr Aquatum-Team</p>
<p style="font-size:12px;color:#7488a0;margin-top:24px">Aquatum AG · Wasser-Experten Schweiz · +41 61 851 00 89 · aquatum.ch</p>
</div></body></html>"""
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": f["EMAIL"], "name": name or f["EMAIL"]}],
        "subject": "Ihr persönlicher Wasserrapport",
        "htmlContent": html,
    }
    return brevo("POST", "/smtp/email", payload)


def send_notify_mail(f):
    """Interne Benachrichtigung an das Team bei jedem Lead (inkl. info@regenfaenger.ch)."""
    recipients = notify_recipients()
    if not SENDER_EMAIL or not recipients:
        return None, "no notify recipient configured"
    name = (f.get("FIRSTNAME", "") + " " + f.get("LASTNAME", "")).strip() or "—"
    fields = [
        ("Produkt", f.get("PRODUKT", "")),
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
<h1 style="font-size:20px;margin:0 0 4px">Neuer Lead · Aquatum</h1>
<p style="margin:0 0 16px;color:#7488a0">{name} · Score {f.get('SCORE', '?')}/100</p>
<table style="width:100%;border-collapse:collapse;font-size:14px">{rows}</table>
<p style="font-size:12px;color:#7488a0;margin-top:20px">Automatische Benachrichtigung von aquatum.ch · Antwort geht direkt an den Lead.</p>
</div></body></html>"""
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": e} for e in recipients],
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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204)

    def _check_admin(self):
        """True, wenn ein gueltiges Bearer-Token im Authorization-Header steht."""
        if not ADMIN_TOKEN:
            return False
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False
        token = auth[7:].strip()
        return bool(token) and hmac.compare_digest(token, ADMIN_TOKEN)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/leads":
            if not self._check_admin():
                time.sleep(1)  # Brute-Force ausbremsen
                return self._send(401, b'{"ok":false,"error":"unauthorized"}')
            leads = read_leads()
            body = json.dumps(
                {"ok": True, "count": len(leads), "leads": leads},
                ensure_ascii=False,
            ).encode("utf-8")
            return self._send(200, body)
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

        # Client-IP (hinter nginx via X-Forwarded-For) bestimmen
        xff = self.headers.get("X-Forwarded-For", "")
        client_ip = xff.split(",")[0].strip() if xff else self.client_address[0]
        client_ua = self.headers.get("User-Agent", "")

        # Lead sofort lokal sichern (Quelle fuer das Admin-Backend) -- auch wenn
        # Brevo gleich darauf einmal haengt, geht der Lead so nie verloren.
        store_lead(f, client_ip)

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
            log(f"[lead] notify OK <{', '.join(notify_recipients())}>")
        elif nstatus is not None:
            log(f"[lead] notify FAIL {nstatus}: {str(nresp)[:200]}")

        # Server-seitiges Lead-Event an Meta (nur bei Einwilligung)
        cstatus, cresp = send_capi_lead(f, client_ip, client_ua)
        if cstatus in (200, 201):
            log(f"[lead] capi OK <{email}> eid={f.get('EVENT_ID','')}")
        elif cstatus is not None:
            log(f"[lead] capi FAIL {cstatus}: {str(cresp)[:200]}")
        else:
            log(f"[lead] capi SKIP ({cresp})")

        self._send(200, b'{"ok":true}')

    def log_message(self, *a):
        pass  # eigenes Logging via log()


def main():
    if not API_KEY:
        log("FATAL: BREVO_API_KEY fehlt"); sys.exit(1)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    log(f"aquatum-leadproxy listening on {HOST}:{PORT} (list={LIST_ID}, sender={SENDER_EMAIL or 'none'}, notify={', '.join(notify_recipients()) or 'none'}, capi={'on:' + META_PIXEL_ID if (META_PIXEL_ID and META_CAPI_TOKEN) else 'off'}, leads_file={LEADS_FILE or 'off'}, admin={'on' if ADMIN_TOKEN else 'OFF (ADMIN_TOKEN fehlt)'})")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
