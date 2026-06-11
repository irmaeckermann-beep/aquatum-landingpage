#!/usr/bin/env python3
"""Erzeugt den 'Wasserrapport' als gebrandete PDF (Regenfänger + Aquatum AG).
Aufruf:  python3 tools/build_wasserrapport.py
Ausgabe: assets/wasserrapport.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, HRFlowable)

BLUE900 = colors.HexColor("#0a2540")
BLUE700 = colors.HexColor("#0e4d8c")
CYAN    = colors.HexColor("#26b9d1")
ORANGE  = colors.HexColor("#ec660b")
INK     = colors.HexColor("#16222e")
MUTED   = colors.HexColor("#5a6b78")
LINE    = colors.HexColor("#dbe6ef")
CYAN50  = colors.HexColor("#eef7fc")
ORANGE10= colors.HexColor("#fdeede")

PAGE_W, PAGE_H = A4
BAND_H = 24 * mm
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "wasserrapport.pdf")


def chrome(canvas, doc):
    canvas.saveState()
    # Kopfband
    canvas.setFillColor(BLUE900)
    canvas.rect(0, PAGE_H - BAND_H, PAGE_W, BAND_H, fill=1, stroke=0)
    y = PAGE_H - 15 * mm
    # Wortmarke Regenfänger
    canvas.setFont("Helvetica-Bold", 15)
    canvas.setFillColor(ORANGE)
    canvas.drawString(18 * mm, y, "regenfänger")
    w = canvas.stringWidth("regenfänger", "Helvetica-Bold", 15)
    canvas.setFillColor(CYAN)
    canvas.drawString(18 * mm + w, y, ".")
    # Trenner
    xd = 18 * mm + w + 8 * mm
    canvas.setStrokeColor(colors.HexColor("#33536f"))
    canvas.setLineWidth(0.8)
    canvas.line(xd, PAGE_H - 18.5 * mm, xd, PAGE_H - 9.5 * mm)
    # Wortmarke Aquatum
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(colors.white)
    canvas.drawString(xd + 6 * mm, y, "AQUATUM")
    wa = canvas.stringWidth("AQUATUM", "Helvetica-Bold", 14)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CYAN)
    canvas.drawString(xd + 6 * mm + wa + 2, y + 1.2 * mm, "AG")
    # rechts
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#9cc2dd"))
    canvas.drawRightString(PAGE_W - 18 * mm, y, "Schweizer Wasser-Experten")
    # Fusszeile
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 11 * mm,
                      "Aquatum AG · Oberdorf 38 A · 4314 Zeiningen · +41 61 851 00 89 · aquatum.ch · regenfaenger.ch")
    canvas.drawRightString(PAGE_W - 18 * mm, 11 * mm, "Seite %d" % doc.page)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(18 * mm, 14 * mm, PAGE_W - 18 * mm, 14 * mm)
    canvas.restoreState()


# Styles
eyebrow = ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=10.5,
                         textColor=ORANGE, spaceAfter=3, leading=13, tracking=1)
h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=32, textColor=BLUE900,
                    leading=34, spaceAfter=8)
subtitle = ParagraphStyle("subtitle", fontName="Helvetica", fontSize=13, textColor=MUTED,
                          leading=18, spaceAfter=16)
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=14.5, textColor=BLUE700,
                    leading=18, spaceBefore=14, spaceAfter=4)
body = ParagraphStyle("body", fontName="Helvetica", fontSize=10.5, textColor=INK,
                      leading=15.5, spaceAfter=8)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=4)
boxhead = ParagraphStyle("boxhead", fontName="Helvetica-Bold", fontSize=11.5, textColor=BLUE900,
                         leading=15, spaceAfter=6)
small = ParagraphStyle("small", fontName="Helvetica", fontSize=8.5, textColor=MUTED, leading=12)
cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13)
cellb = ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=9.5, textColor=BLUE900, leading=13)
cellh = ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.white, leading=13)
white_h = ParagraphStyle("wh", fontName="Helvetica-Bold", fontSize=12, textColor=colors.white, leading=15)
white_b = ParagraphStyle("wb", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#eaf4fb"), leading=14)


def rule(color=LINE, w=0.8, space=10):
    return HRFlowable(width="100%", thickness=w, color=color, spaceBefore=3, spaceAfter=space)


def infobox(title, items):
    inner = [Paragraph(title, boxhead)]
    for it in items:
        inner.append(Paragraph("✓&nbsp;&nbsp;" + it, bullet))
    t = Table([[inner]], colWidths=[PAGE_W - 36 * mm - 8 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CYAN50),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
    ]))
    return t


def solution_block(bg, head, lines):
    inner = [Paragraph(head, white_h)]
    for ln in lines:
        inner.append(Paragraph(ln, white_b))
    t = Table([[inner]], colWidths=[(PAGE_W - 36 * mm - 8) / 2])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    return t


story = []

# ---- Seite 1: Cover ----
story.append(Spacer(1, 14 * mm))
story.append(Paragraph("IHR PERSÖNLICHER", eyebrow))
story.append(Paragraph("Wasserrapport", h1))
story.append(Paragraph("Ihr kompakter Überblick zur Trinkwasserqualität in der Schweiz "
                       "und zu Ihren Möglichkeiten für gesundes, reines Wasser.", subtitle))
story.append(Paragraph(
    "Schweizer Leitungswasser erfüllt strenge Grenzwerte, doch „erlaubt“ ist nicht dasselbe "
    "wie „rein“. Kalk, alte Hausleitungen, Pestizidrückstände, Mikroplastik und Chlor "
    "beeinflussen Qualität, Geschmack und Folgekosten, meist jahrelang unbemerkt. Dieser "
    "Rapport zeigt Ihnen die wichtigsten Fakten und zwei konkrete Wege zu besserem Wasser.", body))
story.append(Spacer(1, 6))
story.append(infobox("Was Sie in diesem Wasserrapport finden:", [
    "Wie sauber Schweizer Leitungswasser wirklich ist",
    "Die vier häufigsten Belastungen und ihre Folgen",
    "Wasserhärte nach Region und was sie kostet",
    "Ihre zwei Lösungen: Wasserfilter und Regenfänger",
    "Ihre nächsten Schritte zur kostenlosen Beratung",
]))
story.append(PageBreak())

# ---- Seite 2 ----
story.append(Spacer(1, 6 * mm))
story.append(Paragraph("Wie sauber ist Schweizer Leitungswasser wirklich?", h2))
story.append(rule())
story.append(Paragraph(
    "Trinkwasser ist das am strengsten kontrollierte Lebensmittel der Schweiz und grundsätzlich "
    "trinkbar. Trotzdem entstehen durch Wasserhärte, alte Leitungen und regionale Belastungen "
    "reale Kosten und Komforteinbussen. Ein Etikett „Grenzwert eingehalten“ sagt nichts darüber "
    "aus, wie weich, wohlschmeckend oder rein Ihr Wasser tatsächlich ist.", body))

story.append(Paragraph("Die vier häufigsten Belastungen", h2))
story.append(rule())
data = [
    [Paragraph("Belastung", cellh), Paragraph("Was dahinter steckt", cellh)],
    [Paragraph("Kalk &amp; hartes Wasser", cell),
     Paragraph("In weiten Teilen der Schweiz über 25&nbsp;°fH. Verstopft Leitungen, "
               "zerstört Geräte, verkürzt die Lebensdauer von Boiler &amp; Co.", cell)],
    [Paragraph("Alte Hausleitungen", cell),
     Paragraph("In Gebäuden vor 1970 noch Blei- und Kupferleitungen. Schwermetalle "
               "können sich im Stehwasser anreichern.", cell)],
    [Paragraph("Pestizid- &amp; Nitratrückstände", cell),
     Paragraph("In landwirtschaftlichen Regionen regelmässig im Grundwasser "
               "nachgewiesen, teils nahe den Grenzwerten.", cell)],
    [Paragraph("Mikroplastik &amp; Chlor", cell),
     Paragraph("Gelangen über Verteilnetze ins Wasser bzw. werden zur Desinfektion "
               "zugesetzt. Beeinflussen Geschmack und Reinheit.", cell)],
]
t = Table(data, colWidths=[48 * mm, (PAGE_W - 36 * mm - 48 * mm)])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), BLUE900),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CYAN50]),
    ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
story.append(t)

story.append(Paragraph("Wasserhärte nach Region", h2))
story.append(rule())
hd = [
    [Paragraph("Härtegrad", cellh), Paragraph("Typische °fH", cellh), Paragraph("Beispiel-Kantone", cellh)],
    [Paragraph("Sehr weich", cell), Paragraph("8–15", cell), Paragraph("TI, UR, GR, OW, GL", cell)],
    [Paragraph("Weich–mittel", cell), Paragraph("16–24", cell), Paragraph("VS, SG, BE, ZH", cell)],
    [Paragraph("Mittel–hart", cell), Paragraph("26–31", cell), Paragraph("GE, ZG, BS, VD, LU, FR", cell)],
    [Paragraph("Hart–sehr hart", cell), Paragraph("34–40", cell), Paragraph("AG, SO, BL, NE, SH, JU", cell)],
]
t2 = Table(hd, colWidths=[40 * mm, 30 * mm, (PAGE_W - 36 * mm - 70 * mm)])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), BLUE700),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CYAN50]),
    ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
]))
story.append(t2)
story.append(Spacer(1, 4))
story.append(Paragraph("Richtwerte je nach Versorgung. Bereits ab ca. 25&nbsp;°fH verursacht "
                       "Kalk spürbare Folgekosten von oft mehreren hundert Franken pro Jahr.", small))
story.append(PageBreak())

# ---- Seite 3 ----
story.append(Spacer(1, 6 * mm))
story.append(Paragraph("Ihre zwei Wege zu gesundem Wasser", h2))
story.append(rule())
story.append(Paragraph(
    "Je nach Wohnsituation passt die eine oder andere Lösung, oder beide kombiniert. "
    "Was für Sie sinnvoll ist, klären wir kostenlos in der persönlichen Beratung.", body))
story.append(Spacer(1, 4))
blocks = Table([[
    solution_block(BLUE700, "Aquatum Wasserfilter", [
        "Für Mietwohnung &amp; Eigenheim",
        "Direkt am Hahn oder fürs ganze Haus",
        "Entfernt Kalk, Chlor &amp; Belastungen",
        "Bis zur Umkehrosmose in Quellqualität",
    ]),
    solution_block(colors.HexColor("#b4500a"), "Regenfänger", [
        "Aus Regenwasser wird Trinkwasser",
        "Bis zu 50% weniger Trinkwasserverbrauch",
        "Unabhängig vom Versorger",
        "Nachhaltig, ideal fürs Eigenheim",
    ]),
]], colWidths=[(PAGE_W - 36 * mm) / 2, (PAGE_W - 36 * mm) / 2])
blocks.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (0, 0), 0),
    ("RIGHTPADDING", (0, 0), (0, 0), 5),
    ("LEFTPADDING", (1, 0), (1, 0), 5),
    ("RIGHTPADDING", (1, 0), (1, 0), 0),
]))
story.append(blocks)

story.append(Paragraph("Ihre nächsten Schritte", h2))
story.append(rule())
for s in [
    "<b>1. Wasser-Check machen:</b> In 60 Sekunden Ihren persönlichen Wasser-Score und Ihre "
    "vermeidbaren Folgekosten ermitteln.",
    "<b>2. Kostenlose Beratung anfordern:</b> Wir analysieren Ihr Wasser vor Ort, unabhängig "
    "und ohne Verkaufsdruck.",
    "<b>3. Passende Lösung wählen:</b> Filter, Regenfänger oder beides, abgestimmt auf Ihren "
    "Haushalt und Ihr Budget.",
]:
    story.append(Paragraph(s, body))

cta = Table([[[
    Paragraph("Jetzt kostenlose Beratung sichern", boxhead),
    Paragraph("<b>Telefon:</b>&nbsp; +41 61 851 00 89 &nbsp;&nbsp;|&nbsp;&nbsp; <b>E-Mail:</b>&nbsp; info@aquatum.ch", body),
    Paragraph("<b>Web:</b>&nbsp; aquatum.ch &nbsp;&nbsp;|&nbsp;&nbsp; regenfaenger.ch", body),
]]], colWidths=[PAGE_W - 36 * mm - 8])
cta.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), ORANGE10),
    ("LEFTPADDING", (0, 0), (-1, -1), 16),
    ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ("TOPPADDING", (0, 0), (-1, -1), 14),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
]))
story.append(Spacer(1, 6))
story.append(cta)
story.append(Spacer(1, 8))
story.append(Paragraph("Dieser Wasserrapport dient der allgemeinen Information. Tatsächliche Werte "
                       "variieren je nach Region, Gebäude und Haushalt. Eine verbindliche Aussage "
                       "liefert die kostenlose Messung vor Ort.", small))

# ---- Build ----
frame = Frame(18 * mm, 16 * mm, PAGE_W - 36 * mm, PAGE_H - BAND_H - 22 * mm, id="main")
doc = BaseDocTemplate(os.path.abspath(OUT), pagesize=A4,
                      title="Wasserrapport – Aquatum AG & Regenfänger",
                      author="Aquatum AG")
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=chrome)])
doc.build(story)
print("written:", os.path.abspath(OUT))
