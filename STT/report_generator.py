import os
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

def add_section(elements, title, content, styles):
    elements.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
    elements.append(Spacer(1, 6))

    if isinstance(content, list):
        if not content:
            elements.append(Paragraph("No data available.", styles["BodyText"]))
        else:
            for item in content:
                elements.append(Paragraph(f"- {str(item)}", styles["BodyText"]))
    else:
        text = str(content).strip()
        if not text:
            text = "No data available."
        elements.append(Paragraph(text, styles["BodyText"]))

    elements.append(Spacer(1, 12))

def generate_pdf(data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title = data.get("title", "AI Generated Report")
    elements.append(Paragraph(f"<b><font size=18>{title}</font></b>", styles["Title"]))
    elements.append(Spacer(1, 16))

    add_section(elements, "Summary", data.get("summary", ""), styles)
    add_section(elements, "Key Topics", data.get("key_topics", []), styles)
    add_section(elements, "Important Points", data.get("important_points", []), styles)
    add_section(elements, "Decisions / Conclusions", data.get("decisions_or_conclusions", []), styles)

    qa_list = []
    for qa in data.get("questions_and_answers", []):
        q = qa.get("question", "")
        a = qa.get("answer", "")
        qa_list.append(f"Q: {q} — A: {a}")

    add_section(elements, "Questions & Answers", qa_list, styles)
    add_section(elements, "Keywords", data.get("keywords", []), styles)

    doc.build(elements)
    print(f"📄 PDF Generated: {output_path}")
