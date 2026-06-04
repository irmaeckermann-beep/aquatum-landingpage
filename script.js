/* =========================================================
   AQUATUM LANDINGPAGE – Konfiguration
   ---------------------------------------------------------
   So verbindest du das Formular mit Brevo:
   1. In Brevo unter "Kontakte > Formulare" ein Anmeldeformular
      erstellen und veröffentlichen.
   2. Die "serve"-URL des Formulars kopieren
      (Form: https://XXXX.sibforms.com/serve/MUIFA...)
      und unten bei BREVO_ENDPOINT einfügen.
   3. In Brevo folgende Kontakt-Attribute anlegen (Typ in Klammern):
      FIRSTNAME (Text), LASTNAME (Text), TELEFON (Text),
      PLZ_ORT (Text), NACHRICHT (Text), SCORE (Zahl),
      HAERTE (Zahl), KOSTEN (Zahl), REGION (Text), PAKET (Text)
   4. Eine Automation erstellen: Auslöser "Kontakt trägt sich in
      Liste ein" -> E-Mail senden mit der Auswertung, z.B.:
      "Ihr Wasser-Score: {{ contact.SCORE }}/100, Härte ca.
      {{ contact.HAERTE }} °fH, Folgekosten CHF {{ contact.KOSTEN }}/Jahr."
   Solange BREVO_ENDPOINT leer ist, läuft die Seite im Demo-Modus
   (Erfolgsmeldung + lokale Speicherung), versendet aber nichts.
   ========================================================= */
const CONFIG = {
  BREVO_ENDPOINT: "/api/lead", // server-seitiger Proxy (server/leadproxy.py) -> Brevo
  LOCALE: "de"
};

// Jahr im Footer
document.getElementById('year').textContent = new Date().getFullYear();

// Referenzen auf Formularfelder
const fScore = document.getElementById('fScore');
const fHaerte = document.getElementById('fHaerte');
const fKosten = document.getElementById('fKosten');
const fRegion = document.getElementById('fRegion');
const fPaket = document.getElementById('fPaket');
const msgField = document.getElementById('message');


// ---------- Wasserqualitäts-Rechner ----------
const calcForm = document.getElementById('calcForm');
const calcResult = document.getElementById('calcResult');
const calcReset = document.getElementById('calcReset');

calcForm.addEventListener('submit', (e) => {
  e.preventDefault();

  const regionSelect = document.getElementById('region');
  const regionVal = regionSelect.value;
  const hardness = parseInt(regionVal, 10);                                   // °fH
  const regionLabel = regionSelect.options[regionSelect.selectedIndex].text;  // Kantonsname
  const persons = parseInt(document.getElementById('persons').value, 10);
  const building = parseFloat(document.getElementById('building').value);     // 0–2 Risiko
  const signs = document.querySelectorAll('input[name="sign"]:checked').length; // 0–4

  // --- Score-Berechnung (100 = perfekt, 0 = stark belastet) ---
  let score = 100;
  score -= Math.min(hardness, 40) * 1.1;        // Härte: bis -44
  score -= building * 9;                          // Leitungsrisiko: bis -18
  score -= signs * 6;                             // Anzeichen: bis -24
  score = Math.max(5, Math.min(100, Math.round(score)));

  // --- geschätzte jährliche Folgekosten ---
  const cost = Math.round((hardness * 11 + signs * 35 + building * 40) * (0.6 + persons * 0.2) / 10) * 10;

  // --- Bewertung ---
  let color, title, text, ctaText;
  if (score >= 75) {
    color = getCss('--good');
    title = 'Solide Wasserqualität mit Optimierungspotenzial';
    text = 'Ihr Wasser ist vergleichsweise gut. Mit gezielten Massnahmen holen Sie noch mehr Komfort und Geräteschutz heraus.';
    ctaText = 'Kostenlose Detail-Analyse anfordern →';
  } else if (score >= 50) {
    color = getCss('--warn');
    title = 'Spürbare Belastung, Handlungsbedarf empfohlen';
    text = 'Kalk und/oder weitere Faktoren belasten Ihr Wasser merklich. Eine passende Aufbereitung schützt Geräte und Geldbeutel.';
    ctaText = 'Jetzt kostenlose Analyse sichern →';
  } else {
    color = getCss('--bad');
    title = 'Deutliche Belastung, wir empfehlen eine Analyse';
    text = 'Mehrere Faktoren sprechen für eine erhöhte Belastung Ihres Wassers. Eine professionelle Messung vor Ort schafft Klarheit.';
    ctaText = 'Gratis-Analyse dringend empfohlen →';
  }

  // --- Score-Ring rendern ---
  const ring = document.getElementById('scoreRing');
  const deg = (score / 100) * 360;
  ring.style.background = `conic-gradient(${color} ${deg}deg, var(--line) ${deg}deg)`;

  document.getElementById('scoreNumber').textContent = score;
  document.getElementById('resultTitle').textContent = title;
  document.getElementById('resultText').textContent = text;
  document.getElementById('hardnessVal').textContent = hardness;
  document.getElementById('costVal').textContent = 'CHF ' + cost;
  document.getElementById('resultCta').textContent = ctaText;

  // --- Werte ins Anmeldeformular übergeben (versteckte Brevo-Felder) ---
  fScore.value = score;
  fHaerte.value = hardness;
  fKosten.value = cost;
  fRegion.value = regionLabel;
  if (msgField && !msgField.value) {
    msgField.value = `Mein Wasser-Score: ${score}/100 · Härte ca. ${hardness} °fH · geschätzte Folgekosten CHF ${cost}/Jahr · Region: ${regionLabel}.`;
  }

  // --- Anzeige umschalten (Formular bleibt sichtbar, Platzhalter -> Ergebnis) ---
  document.getElementById('calcPlaceholder').hidden = true;
  calcResult.hidden = false;
});

calcReset.addEventListener('click', () => {
  calcResult.hidden = true;
  document.getElementById('calcPlaceholder').hidden = false;
  calcForm.reset();
  calcForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
});

function getCss(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
}

// ---------- Paket-CTAs ("Konzepte verkaufen") ----------
document.querySelectorAll('.pkg-cta').forEach((btn) => {
  btn.addEventListener('click', () => {
    const paket = btn.getAttribute('data-paket');
    fPaket.value = paket;
    if (msgField) {
      const note = `Ich interessiere mich für das Konzept «${paket}».`;
      msgField.value = msgField.value ? `${msgField.value}\n${note}` : note;
    }
    document.getElementById('anmeldung').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('firstName').focus({ preventScroll: true });
  });
});

// ---------- Anmeldeformular (Brevo) ----------
const signupForm = document.getElementById('signupForm');
const formSuccess = document.getElementById('formSuccess');
const formError = document.getElementById('formError');
const submitBtn = document.getElementById('signupSubmit');

signupForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  formError.hidden = true;

  // Honeypot: wenn ausgefüllt -> stiller Abbruch (Bot)
  if (signupForm.querySelector('[name="email_address_check"]').value) return;

  // Pflichtfelder prüfen
  const required = ['firstName', 'lastName', 'email', 'phone', 'zip', 'consent'];
  for (const id of required) {
    const el = document.getElementById(id);
    const ok = el.type === 'checkbox' ? el.checked : el.value.trim() !== '';
    if (!ok) {
      showError('Bitte füllen Sie alle Pflichtfelder aus und bestätigen Sie den Datenschutz.');
      el.focus();
      return;
    }
  }
  const email = document.getElementById('email').value.trim();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showError('Bitte geben Sie eine gültige E-Mail-Adresse ein.');
    document.getElementById('email').focus();
    return;
  }

  // Daten einsammeln
  const data = new URLSearchParams();
  new FormData(signupForm).forEach((value, key) => data.append(key, value));
  data.append('locale', CONFIG.LOCALE);

  // Lokales Backup (geht nie verloren, exportierbar via exportLeads())
  saveLeadLocally(Object.fromEntries(data));

  submitBtn.disabled = true;
  submitBtn.textContent = 'Wird angemeldet…';

  try {
    if (CONFIG.BREVO_ENDPOINT) {
      await fetch(CONFIG.BREVO_ENDPOINT, {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data.toString()
      });
      // no-cors liefert keine lesbare Antwort -> optimistisch als Erfolg werten
    }
    // Weiterleitung auf die Dankesseite (= Conversion-/Lead-Seite, loest dort den Lead-Event aus)
    window.location.href = 'danke.html';
    return;
  } catch (err) {
    showError('Es gab ein Problem bei der Anmeldung. Bitte versuchen Sie es erneut oder rufen Sie uns an: +41 61 851 00 89.');
    submitBtn.disabled = false;
    submitBtn.textContent = 'Jetzt anmelden & Auswertung erhalten';
  }
});

function showError(text) {
  formError.textContent = text;
  formError.hidden = false;
}

// Lokales Lead-Backup (Fallback / Test)
function saveLeadLocally(obj) {
  try {
    const leads = JSON.parse(localStorage.getItem('aquatum_leads') || '[]');
    leads.push({ ...obj, ts: new Date().toISOString() });
    localStorage.setItem('aquatum_leads', JSON.stringify(leads));
  } catch (e) { /* localStorage evtl. nicht verfügbar */ }
}

// In der Browser-Konsole aufrufbar: exportLeads() -> lädt alle Leads als CSV
window.exportLeads = function () {
  const leads = JSON.parse(localStorage.getItem('aquatum_leads') || '[]');
  if (!leads.length) { console.log('Keine Leads gespeichert.'); return; }
  const cols = Object.keys(leads.reduce((a, l) => ({ ...a, ...l }), {}));
  const csv = [cols.join(';')]
    .concat(leads.map(l => cols.map(c => `"${(l[c] || '').toString().replace(/"/g, '""')}"`).join(';')))
    .join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  const a = document.createElement('a');
  a.href = url; a.download = 'aquatum-leads.csv'; a.click();
};
