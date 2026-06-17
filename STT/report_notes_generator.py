import os
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
                # If item is dict -> convert to "key: value — key2: value2"
                if isinstance(item, dict):
                    pairs = []
                    for k, v in item.items():
                        # Clean nested newlines/long text into single line
                        val = str(v).replace("\n", " ").strip()
                        pairs.append(f"{k}: {val}")
                    line = " — ".join(pairs)
                    elements.append(Paragraph(f"- {line}", styles["BodyText"]))
                else:
                    text = str(item).replace("\n", " ").strip()
                    elements.append(Paragraph(f"- {text}", styles["BodyText"]))
    else:
        text = str(content).replace("\n", " ").strip()
        if text == "":
            text = "No data available."
        elements.append(Paragraph(text, styles["BodyText"]))
    elements.append(Spacer(1, 12))


def generate_notes_pdf(notes_json, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title = notes_json.get("lecture_title", "Lecture Notes")
    elements.append(Paragraph(f"<b><font size=18>{title}</font></b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    add_section(elements, "Topics Covered", notes_json.get("topics", []), styles)
    add_section(elements, "Subtopics", notes_json.get("subtopics", []), styles)
    add_section(elements, "Key Points", notes_json.get("key_points", []), styles)
    add_section(elements, "Definitions", notes_json.get("definitions", []), styles)
    add_section(elements, "Examples", notes_json.get("examples", []), styles)
    add_section(elements, "Summary", notes_json.get("summary", "N/A"), styles)
    add_section(elements, "Keywords", notes_json.get("keywords", []), styles)

    doc.build(elements)
