"""
generate_pdf.py
---------------
Generates a clean, formatted PDF report of the top 10 stock recommendations.
Saves to reports/top10_YYYY-MM-DD.pdf

Usage:
    python tools/generate_pdf.py

File inputs:
    .tmp/top10.json

Outputs:
    reports/top10_YYYY-MM-DD.pdf
"""

import os
import json
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

INPUT_PATH = ".tmp/top10.json"
OUTPUT_DIR = "reports"

SENTIMENT_COLORS = {
    "positive": colors.HexColor("#1a7a3c"),
    "negative": colors.HexColor("#c0392b"),
    "neutral":  colors.HexColor("#7f8c8d"),
}


def sentiment_label(s: str) -> str:
    return {"positive": "▲ Bullish", "negative": "▼ Bearish", "neutral": "● Neutral"}.get(s, s)


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[generate_pdf] Input not found: {INPUT_PATH}. Run generate_top10.py first.")
        return

    with open(INPUT_PATH, encoding="utf-8") as f:
        top10 = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = str(date.today())
    output_path = os.path.join(OUTPUT_DIR, f"top10_{today}.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Title ---
    title_style = ParagraphStyle(
        "Title",
        fontSize=22,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontSize=11,
        fontName="Helvetica",
        textColor=colors.HexColor("#555555"),
        spaceAfter=2,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        fontSize=8,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#999999"),
        spaceAfter=10,
    )

    story.append(Paragraph("Top 10 Stock Picks", title_style))
    story.append(Paragraph(f"News-driven analysis — {today}", subtitle_style))
    story.append(Paragraph(
        "For research and informational purposes only. Not financial advice.",
        disclaimer_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 6 * mm))

    # --- Summary Table ---
    table_data = [[
        "#", "Ticker", "Company", "Score", "Sentiment", "Price", "Chg %"
    ]]
    for s in top10:
        price = f"${s['price']:.2f}" if s.get("price") else "—"
        chg = f"{s['change_pct']:+.2f}%" if s.get("change_pct") is not None else "—"
        table_data.append([
            str(s["rank"]),
            s["ticker"],
            s["company"][:28],
            f"{s['composite_score']:.4f}",
            sentiment_label(s.get("sentiment", "neutral")),
            price,
            chg,
        ])

    col_widths = [10 * mm, 18 * mm, 60 * mm, 22 * mm, 28 * mm, 20 * mm, 18 * mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 8 * mm))

    # --- Detail Cards ---
    card_title_style = ParagraphStyle(
        "CardTitle",
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=2,
    )
    card_body_style = ParagraphStyle(
        "CardBody",
        fontSize=8.5,
        fontName="Helvetica",
        textColor=colors.HexColor("#333333"),
        spaceAfter=2,
        leading=13,
    )
    risk_style = ParagraphStyle(
        "Risk",
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#c0392b"),
        spaceAfter=4,
    )

    for s in top10:
        sent_color = SENTIMENT_COLORS.get(s.get("sentiment", "neutral"), colors.grey)
        story.append(Paragraph(
            f"#{s['rank']} &nbsp; {s['ticker']} — {s['company']}",
            card_title_style
        ))
        story.append(Paragraph(
            f"<font color='#{sent_color.hexval()[2:]}' ><b>{sentiment_label(s.get('sentiment','neutral'))}</b></font> &nbsp;|&nbsp; Score: {s['composite_score']:.4f} &nbsp;|&nbsp; Articles analysed: {s.get('article_count', '—')}",
            card_body_style
        ))
        story.append(Paragraph(f"<b>Key driver:</b> {s.get('key_news', '—')}", card_body_style))
        story.append(Paragraph(f"<b>Why it matters:</b> {s.get('impact_reason', '—')}", card_body_style))
        story.append(Paragraph(f"<b>Source:</b> {s.get('source', '—')} &nbsp; <b>URL:</b> {s.get('url', '—')}", card_body_style))
        if s.get("risk_note"):
            story.append(Paragraph(f"⚠ {s['risk_note']}", risk_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#eeeeee")))
        story.append(Spacer(1, 4 * mm))

    doc.build(story)
    print(f"[generate_pdf] Report saved to {output_path}")


if __name__ == "__main__":
    main()
