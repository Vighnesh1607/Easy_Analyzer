from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

def analyze_notes(transcript):

    prompt = f"""
You are an AI that generates structured lecture notes from a transcript.

IMPORTANT RULES:
- NEVER censor or redact text.
- NEVER use black boxes (■).
- If unclear, write "Not clearly heard".
- Do NOT remove or hide information.
- Return ONLY valid JSON. No markdown fences or extra commentary.

Transcript:
{transcript}

Return EXACT JSON:
{{
  "lecture_title": "",
  "topics": [],
  "subtopics": [],
  "key_points": [],
  "definitions": [],
  "examples": [],
  "summary": "",
  "keywords": []
}}
"""

    resp = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return resp.choices[0].message.content
