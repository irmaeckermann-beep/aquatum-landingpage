# Brevo einrichten – Schritt für Schritt

Ziel: Wenn sich jemand auf der Landingpage anmeldet, soll
1. **der Lead automatisch seine Wasser-Auswertung per E-Mail bekommen** und
2. **du seine Kontaktdaten in Brevo sehen** (inkl. Score, Härte, Kosten).

Dauer: ca. 20–30 Minuten. Alles im kostenlosen Brevo-Tarif machbar.

---

## Schritt 1 – Konto & Liste

1. Konto erstellen auf [brevo.com](https://www.brevo.com) (falls noch nicht vorhanden).
2. Links im Menü **Kontakte → Listen → Liste hinzufügen**.
3. Liste benennen, z. B. **`Landingpage Leads`**. Notiere dir den Namen.

---

## Schritt 2 – Kontakt-Attribute anlegen

Damit Score & Co. gespeichert und in der E-Mail angezeigt werden können.

**Kontakte → Einstellungen → Kontakt-Attribute → Attribut hinzufügen.**

Lege diese Attribute an (Name **exakt** so schreiben, Gross-/Kleinschreibung beachten):

| Attribut-Name | Typ      |
|---------------|----------|
| `FIRSTNAME`   | Text     | (existiert meist schon = «Vorname») |
| `LASTNAME`    | Text     | (existiert meist schon = «Nachname») |
| `TELEFON`     | Text     |
| `PLZ_ORT`     | Text     |
| `NACHRICHT`   | Text     |
| `SCORE`       | Zahl     |
| `HAERTE`      | Zahl     |
| `KOSTEN`      | Zahl     |
| `REGION`      | Text     |
| `PAKET`       | Text     |

> Wichtig: Die Namen müssen **genau** mit den `name="…"`-Feldern im Formular übereinstimmen.

---

## Schritt 3 – Anmeldeformular in Brevo erstellen

1. **Kontakte → Formulare → Ein Formular erstellen**.
2. Alle oben genannten Felder ins Formular ziehen (Vorname, Nachname, E-Mail, TELEFON, PLZ_ORT, NACHRICHT, SCORE, HAERTE, KOSTEN, REGION, PAKET). Die Score-Felder kannst du auf **versteckt** stellen.
3. Bei **«Kontakt zu dieser Liste hinzufügen»** die Liste **`Landingpage Leads`** wählen.
4. Optional **Double-Opt-in** aktivieren (rechtssicher; der Lead bestätigt per Klick in einer Mail).
5. Formular **speichern & veröffentlichen**.
6. Im Reiter **«Teilen» / «Einbetten»** findest du die **serve-URL**. Sie sieht so aus:
   ```
   https://XXXXX.sibforms.com/serve/MUIFAxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   Diese URL kopieren.

---

## Schritt 4 – URL in die Seite eintragen

Datei **`script.js`** öffnen, ganz oben:

```js
const CONFIG = {
  BREVO_ENDPOINT: "https://XXXXX.sibforms.com/serve/MUIFA...", // <-- hier deine URL
  LOCALE: "de"
};
```

Speichern. Ab jetzt landen echte Anmeldungen in Brevo.
(Solange das Feld leer ist, läuft die Seite im Demo-Modus.)

---

## Schritt 5 – Automation: Auto-Antwort mit Auswertung

1. **Automationen → Automation erstellen → Eigener Workflow** (oder Vorlage «Willkommens-E-Mail»).
2. **Auslöser/Einstiegspunkt:** «Ein Kontakt tritt einer Liste bei» → Liste **`Landingpage Leads`**.
3. Schritt hinzufügen: **«Eine E-Mail senden»** → neue E-Mail gestalten (Text siehe unten).
4. Automation **aktivieren**.

Fertig. Jeder neue Lead bekommt sofort seine Auswertung, du siehst ihn unter **Kontakte**.

---

## Auto-Antwort E-Mail – fertiger Text

**Betreff:**
```
Ihre persönliche Wasser-Auswertung von Aquatum
```

**Inhalt (Personalisierungs-Tags in {{ }} ersetzt Brevo automatisch):**

```
Hallo {{ contact.FIRSTNAME }}

vielen Dank für Ihren Wasser-Check auf aquatum.ch. Hier ist Ihre persönliche Auswertung:

────────────────────────────
Ihr Wasser-Score: {{ contact.SCORE }} / 100
Geschätzte Wasserhärte: ca. {{ contact.HAERTE }} °fH
Vermeidbare Folgekosten: rund CHF {{ contact.KOSTEN }} pro Jahr
Region: {{ contact.REGION }}
────────────────────────────

Was bedeutet das?
Je tiefer der Score, desto stärker belasten Kalk, alte Leitungen oder
regionale Faktoren Ihr Wasser – und desto grösser ist Ihr Sparpotenzial
bei Geräten, Energie und Reinigungsmitteln.

Ihr nächster Schritt – kostenlos & unverbindlich:
Einer unserer Wasser-Experten meldet sich innert 24 Stunden bei Ihnen,
bespricht Ihr Ergebnis und empfiehlt – falls gewünscht – die passende Lösung
für Ihren Haushalt.

Sie möchten direkt einen Termin?
Telefon: +41 61 851 00 89
E-Mail:  info@aquatum.ch

Herzliche Grüsse
Ihr Aquatum-Team

Aquatum AG · Oberdorf 38 A · CH-4314 Zeiningen · www.aquatum.ch
```

> Tipp: Falls ein Lead das Formular ohne Rechner ausfüllt, sind SCORE/HAERTE/KOSTEN leer.
> In Brevo kannst du mit einer Bedingung («Wenn SCORE nicht leer») zwei E-Mail-Varianten
> senden – eine mit Auswertung, eine allgemeine Begrüssung.

---

## Schritt 6 – Testen

1. Seite im Browser öffnen, Wasser-Check ausfüllen, dann das Anmeldeformular mit einer
   **eigenen Test-E-Mail** absenden.
2. In Brevo unter **Kontakte** prüfen: Ist der Kontakt mit SCORE/HAERTE/KOSTEN da?
3. Postfach prüfen: Ist die Auswertungs-Mail angekommen?
   (Bei Double-Opt-in zuerst den Bestätigungslink klicken.)

---

## Backup / Notfall

Alle Anmeldungen werden zusätzlich lokal im Browser gespeichert.
Falls nötig, in der Browser-Konsole (F12) eingeben:

```js
exportLeads()
```

→ lädt alle gesammelten Leads als CSV-Datei herunter.
