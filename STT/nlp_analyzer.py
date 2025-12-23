from groq import Groq
import os
import json
import re

client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))


def clean_json_output(raw):
    """Strip fences and extract JSON object (first {})."""
    if not isinstance(raw, str):
        try:
            raw = json.dumps(raw)
        except:
            raw = str(raw)

    raw = raw.replace("```json", "").replace("```", "").strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    return m.group(0) if m else raw


def normalize_keys(data):
    new = {}
    for k, v in data.items():
        nk = k.strip().lower().replace(" ", "_")
        new[nk] = v
    return new


def analyze_transcript(text):
    prompt = f"""
You are an AI that extracts meaningful and structured information from transcripts.

VERY IMPORTANT RULES:
- NEVER censor, redact, or use black boxes (■).
- NEVER invent facts. If something is not present say "Not clearly heard".
- Preserve punctuation and numbers as-is.
- Return ONLY valid JSON. No markdown fences, no extra text.

Transcript:
{text}

Return EXACT JSON with these keys only:
{{
  "title": "",
  "summary": "",
  "key_topics": [],
  "important_points": [],
  "decisions_or_conclusions": [],
  "questions_and_answers": [],
  "keywords": []
}}
"""

    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25
    )

    return response.choices[0].message.content
