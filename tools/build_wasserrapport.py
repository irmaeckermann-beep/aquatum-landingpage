#!/usr/bin/env python3
"""Erzeugt den 'Wasserrapport' als plakative, gebrandete PDF
(Regenfänger + Aquatum AG). Grosse Farbflächen, fette Schlagzeilen, grosse Zahlen.
Aufruf:  python3 tools/build_wasserrapport.py   ->  assets/wasserrapport.pdf
"""
import io
import os
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, Image as RLImage)

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")


def banner(filename, height_mm, width=None):
    """Schneidet ein Foto mittig auf Banner-Format zu und gibt ein RLImage zurück."""
    w = width if width is not None else (PAGE_W - 2 * MARGIN)
    h = height_mm * mm
    img = PILImage.open(os.path.join(ASSETS, filename)).convert("RGB")
    iw, ih = img.size
    aspect = w / h
    if iw / ih > aspect:
        nw = int(ih * aspect); x0 = (iw - nw) // 2
        img = img.crop((x0, 0, x0 + nw, ih))
    else:
        nh = int(iw / aspect); y0 = (ih - nh) // 2
        img = img.crop((0, y0, iw, y0 + nh))
    bio = io.BytesIO()
    img.save(bio, format="JPEG", quality=86)
    bio.seek(0)
    return RLImage(bio, width=w, height=h)


def image_w(filename, width):
    """Bild auf gegebene Breite skalieren (Seitenverhältnis erhalten), zentriert."""
    p = os.path.join(ASSETS, filename)
    pw, ph = PILImage.open(p).size
    im = RLImage(p, width=width, height=width * ph / pw)
    im.hAlign = "CENTER"
    return im

BLUE900 = colors.HexColor("#0a2540")
BLUE700 = colors.HexColor("#0e4d8c")
BLUE500 = colors.HexColor("#1488d8")
CYAN    = colors.HexColor("#26b9d1")
ORANGE  = colors.HexColor("#ec660b")
ORANGED = colors.HexColor("#b4500a")
INK     = colors.HexColor("#16222e")
MUTED   = colors.HexColor("#5a6b78")
LINE    = colors.HexColor("#dbe6ef")
CYAN50  = colors.HexColor("#eef7fc")
WHITE   = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
BAND_H = 18 * mm
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "wasserrapport.pdf")


def chrome(canvas, doc):
    canvas.saveState()
    # schlankes Kopfband mit Wortmarken
    canvas.setFillColor(BLUE900)
    canvas.rect(0, PAGE_H - BAND_H, PAGE_W, BAND_H, fill=1, stroke=0)
    y = PAGE_H - 11.5 * mm
    canvas.setFont("Helvetica-Bold", 12)
    canvas.setFillColor(ORANGE)
    canvas.drawString(MARGIN, y, "regenfänger")
    w = canvas.stringWidth("regenfänger", "Helvetica-Bold", 12)
    canvas.setFillColor(CYAN)
    canvas.drawString(MARGIN + w, y, ".")
    xd = MARGIN + w + 7 * mm
    canvas.setStrokeColor(colors.HexColor("#33536f"))
    canvas.setLineWidth(0.8)
    canvas.line(xd, PAGE_H - 14 * mm, xd, PAGE_H - 7 * mm)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.setFillColor(WHITE)
    canvas.drawString(xd + 5 * mm, y, "AQUATUM")
    wa = canvas.stringWidth("AQUATUM", "Helvetica-Bold", 11)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CYAN)
    canvas.drawString(xd + 5 * mm + wa + 2, y + 1 * mm, "AG")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#9cc2dd"))
    canvas.drawRightString(PAGE_W - MARGIN, y, "aus Regen zum Trinkwasser")
    # Fusszeile
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 9 * mm,
                      "Aquatum AG · Oberdorf 38 A · 4314 Zeiningen · +41 61 851 00 89 · aquatum.ch · regenfaenger.ch")
    canvas.drawRightString(PAGE_W - MARGIN, 9 * mm, "%d / 3" % doc.page)
    canvas.restoreState()


# ---------- Styles ----------
def ps(name, **kw):
    return ParagraphStyle(name, **kw)

mega   = ps("mega", fontName="Helvetica-Bold", fontSize=46, leading=46, textColor=WHITE)
eyebrowW = ps("eyebrowW", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=ORANGE)
subW   = ps("subW", fontName="Helvetica", fontSize=13, leading=18, textColor=colors.HexColor("#d8eef9"))
h2     = ps("h2", fontName="Helvetica-Bold", fontSize=22, leading=24, textColor=BLUE900)
h2W    = ps("h2W", fontName="Helvetica-Bold", fontSize=22, leading=24, textColor=WHITE)
body   = ps("body", fontName="Helvetica", fontSize=10.5, leading=15.5, textColor=INK)
lead   = ps("lead", fontName="Helvetica", fontSize=12, leading=17, textColor=INK)
statNum = ps("statNum", fontName="Helvetica-Bold", fontSize=30, leading=30, textColor=WHITE, alignment=1)
statLbl = ps("statLbl", fontName="Helvetica", fontSize=8.5, leading=11, textColor=WHITE, alignment=1)
cardTitle = ps("cardTitle", fontName="Helvetica-Bold", fontSize=13.5, leading=16, textColor=WHITE)
cardBody  = ps("cardBody", fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#eaf4fb"))
panelH = ps("panelH", fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=WHITE)
panelLi = ps("panelLi", fontName="Helvetica", fontSize=10.5, leading=15, textColor=colors.HexColor("#eaf4fb"))
checkLi = ps("checkLi", fontName="Helvetica", fontSize=11, leading=17, textColor=INK)
ctaH = ps("ctaH", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=ORANGED)
small = ps("small", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED)
stepN = ps("stepN", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=ORANGE)


def block(content, bg, pad=16, radius=10, lpad=None, rpad=None, tpad=None, bpad=None):
    t = Table([[content]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), lpad if lpad is not None else pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), rpad if rpad is not None else pad),
        ("TOPPADDING", (0, 0), (-1, -1), tpad if tpad is not None else pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), bpad if bpad is not None else pad),
    ]))
    return t


def stat_box(bg, num, label):
    inner = [Paragraph(num, statNum), Spacer(1, 3), Paragraph(label, statLbl)]
    t = Table([[inner]], colWidths=[(CONTENT_W - 16) / 3.0])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def stat_row(items):
    cells = [stat_box(*it) for it in items]
    row = Table([[cells[0], "", cells[1], "", cells[2]]],
                colWidths=[(CONTENT_W - 16) / 3.0, 8, (CONTENT_W - 16) / 3.0, 8, (CONTENT_W - 16) / 3.0])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return row


def card(bg, title, text):
    inner = [Paragraph(title, cardTitle), Spacer(1, 5), Paragraph(text, cardBody)]
    t = Table([[inner]], colWidths=[(CONTENT_W - 10) / 2.0])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    return t


def card_row(left, right):
    row = Table([[left, "", right]], colWidths=[(CONTENT_W - 10) / 2.0, 10, (CONTENT_W - 10) / 2.0])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return row


story = []

# ============ SEITE 1 – COVER ============
hero_inner = [
    Paragraph("IHR PERSÖNLICHER", eyebrowW),
    Spacer(1, 2),
    Paragraph("WASSER-", mega),
    Paragraph("RAPPORT", mega),
    Spacer(1, 10),
    Paragraph("Ihr kompakter Überblick zur Trinkwasserqualität in der Schweiz, "
              "und zu zwei klaren Wegen zu gesundem, reinem Wasser.", subW),
]
story.append(block(hero_inner, BLUE900, lpad=26, rpad=26, tpad=28, bpad=28))
story.append(Spacer(1, 10))
story.append(banner("hero-wasser.jpg", 48))
story.append(Spacer(1, 12))
story.append(stat_row([
    (BLUE500, "1 von 3", "Schweizer Haushalten lebt mit sehr hartem Wasser"),
    (ORANGE, "bis 50%", "weniger Trinkwasser-verbrauch dank Regenwasser"),
    (CYAN, "~CHF 500", "vermeidbare Folgekosten pro Haushalt &amp; Jahr"),
]))
story.append(Spacer(1, 14))
tag = block([Paragraph("„Erlaubt“ ist nicht „rein“: Dieser Rapport zeigt Ihnen die Fakten "
                       "zu Ihrem Wasser, und Ihre zwei Lösungen für gesundes, reines Wasser.",
                       ps("tag", fontName="Helvetica-Bold", fontSize=13, leading=18, textColor=BLUE900))],
            CYAN50, lpad=18, rpad=18, tpad=14, bpad=14)
tag.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), CYAN50),
    ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18),
    ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ("LINEBEFORE", (0, 0), (0, -1), 4, ORANGE),
]))
story.append(tag)
story.append(PageBreak())

# ============ SEITE 2 – BELASTUNGEN ============
story.append(Spacer(1, 4))
story.append(Paragraph("Die 4 grössten Wasser-Belastungen", h2))
story.append(Spacer(1, 12))
story.append(card_row(
    card(BLUE700, "Kalk &amp; hartes Wasser",
         "In weiten Teilen der Schweiz über 25 °fH. Verstopft Leitungen, zerstört Geräte "
         "und verkürzt deren Lebensdauer erheblich."),
    card(BLUE500, "Alte Hausleitungen",
         "In Gebäuden vor 1970 noch Blei- und Kupferleitungen. Schwermetalle können sich "
         "im Stehwasser anreichern, kritisch für Kinder."),
))
story.append(Spacer(1, 10))
story.append(card_row(
    card(CYAN, "Pestizid- &amp; Nitratrückstände",
         "In landwirtschaftlichen Regionen regelmässig im Grundwasser nachgewiesen, "
         "teils nahe den Grenzwerten."),
    card(ORANGE, "Mikroplastik &amp; Chlor",
         "Gelangen über Verteilnetze ins Wasser oder werden zur Desinfektion zugesetzt. "
         "Beeinflussen Geschmack und Reinheit."),
))
story.append(Spacer(1, 22))
story.append(Paragraph("Wo das Wasser am härtesten ist", h2))
story.append(Spacer(1, 8))
story.append(image_w("wasserhaerte-karte.png", 150 * mm))
story.append(Spacer(1, 6))
story.append(Paragraph("Je dunkler, desto härter: Besonders betroffen sind <b>Jura, Schaffhausen, "
                       "Basel-Landschaft, Neuenburg, Solothurn und Aargau</b> sowie das Mittelland. "
                       "Weich ist das Wasser vor allem im Tessin, in Graubünden und am Alpenrand. "
                       "Schon ab ca. 25 °fH verursacht Kalk spürbare Folgekosten.", body))
story.append(PageBreak())

# ============ SEITE 3 – LÖSUNGEN ============
story.append(Spacer(1, 4))
story.append(Paragraph("Ihre 2 Wege zu gesundem Wasser", h2))
story.append(Spacer(1, 12))

def panel(bg, head, lines):
    inner = [Paragraph(head, panelH), Spacer(1, 8)]
    for ln in lines:
        inner.append(Paragraph("✓&nbsp;&nbsp;" + ln, panelLi))
    t = Table([[inner]], colWidths=[(CONTENT_W - 10) / 2.0])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
    ]))
    return t

prow = Table([[
    panel(BLUE700, "AQUATUM WASSERFILTER", [
        "Für Mietwohnung &amp; Eigenheim",
        "Direkt am Hahn oder fürs ganze Haus",
        "Entfernt Kalk, Chlor &amp; Belastungen",
        "Bis zur Umkehrosmose in Quellqualität",
    ]),
    "",
    panel(ORANGED, "REGENFÄNGER", [
        "Aus Regenwasser wird Trinkwasser",
        "Bis zu 50% weniger Trinkwasser",
        "Unabhängig vom Versorger",
        "Nachhaltig, ideal fürs Eigenheim",
    ]),
]], colWidths=[(CONTENT_W - 10) / 2.0, 10, (CONTENT_W - 10) / 2.0])
prow.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(prow)
story.append(Spacer(1, 16))
story.append(banner("experte-beratung.jpg", 36))
story.append(Spacer(1, 16))

story.append(Paragraph("In 3 Schritten zum Ziel", h2))
story.append(Spacer(1, 12))
steps = [
    ("1", "Wasser-Check machen", "In 60 Sekunden Ihren persönlichen Wasser-Score und Ihre vermeidbaren Folgekosten ermitteln."),
    ("2", "Kostenlose Beratung", "Wir analysieren Ihr Wasser vor Ort, unabhängig und ohne Verkaufsdruck."),
    ("3", "Passende Lösung wählen", "Filter, Regenfänger oder beides, abgestimmt auf Ihren Haushalt und Ihr Budget."),
]
for n, t, d in steps:
    cell = [[Paragraph(n, ps("bignum", fontName="Helvetica-Bold", fontSize=22, textColor=ORANGE, alignment=1)),
             [Paragraph("<b>" + t + "</b>", ps("st", fontName="Helvetica-Bold", fontSize=12, textColor=BLUE900, spaceAfter=2)),
              Paragraph(d, body)]]]
    st = Table(cell, colWidths=[16 * mm, CONTENT_W - 16 * mm])
    st.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (0, 0), CYAN50),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(st)
    story.append(Spacer(1, 7))

story.append(Spacer(1, 8))
cta_inner = [
    Paragraph("Jetzt kostenlose Beratung sichern", ctaH),
    Spacer(1, 6),
    Paragraph("<b>Telefon</b> +41 61 851 00 89 &nbsp;&nbsp;·&nbsp;&nbsp; <b>E-Mail</b> info@aquatum.ch "
              "&nbsp;&nbsp;·&nbsp;&nbsp; <b>Web</b> aquatum.ch &nbsp;|&nbsp; regenfaenger.ch", body),
]
cta = Table([[cta_inner]], colWidths=[CONTENT_W])
cta.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdeede")),
    ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18),
    ("TOPPADDING", (0, 0), (-1, -1), 16), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ("LINEBEFORE", (0, 0), (0, -1), 4, ORANGE),
]))
story.append(cta)

# ---------- Build ----------
frame = Frame(MARGIN, 13 * mm, CONTENT_W, PAGE_H - BAND_H - 18 * mm, id="main")
doc = BaseDocTemplate(os.path.abspath(OUT), pagesize=A4,
                      title="Wasserrapport – Aquatum AG & Regenfänger", author="Aquatum AG")
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=chrome)])
doc.build(story)
print("written:", os.path.abspath(OUT))
