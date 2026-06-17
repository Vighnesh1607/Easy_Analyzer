import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq

# ----------------------------
# GLOBALS
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPT_FOLDER = os.path.join(BASE_DIR, "transcripts")
INDEX_FILE = os.path.join(BASE_DIR, "rag_index.json")

client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

# ⭐ Multilingual embedding model (Hindi + English understanding)
embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


# ----------------------------
# LOAD / SAVE INDEX
# ----------------------------
def load_index():
    if not os.path.exists(INDEX_FILE):
        return {"documents": []}
    return json.load(open(INDEX_FILE, "r", encoding="utf-8"))


def save_index(index):
    json.dump(index, open(INDEX_FILE, "w", encoding="utf-8"),
              indent=4, ensure_ascii=False)


# ----------------------------
# CHUNKING
# ----------------------------
def chunk_text(text, max_words=120):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
        i += max_words
    return chunks


# ----------------------------
# BUILD INDEX FOR ONE SESSION
# ----------------------------
def build_index_for_session(session_id):
    index = load_index()

    txt_path = os.path.join(TRANSCRIPT_FOLDER, f"{session_id}.txt")
    if not os.path.exists(txt_path):
        return {"error": f"Transcript not found: {session_id}"}

    text = open(txt_path, "r", encoding="utf-8").read().strip()
    chunks = chunk_text(text)

    for i, c in enumerate(chunks):
        try:
            vec = embedder.encode([c])[0].tolist()
            entry = {
                "session_id": session_id,
                "chunk_id": i,
                "chunk": c,
                "embedding": vec
            }
            index["documents"].append(entry)
        except Exception as e:
            return {"error": str(e)}

    save_index(index)
    return {"status": "ok", "chunks": len(chunks)}


# ----------------------------
# BUILD INDEX FOR ALL SESSIONS
# ----------------------------
def build_index_from_all():
    save_index({"documents": []})  # RESET INDEX

    files = [f for f in os.listdir(TRANSCRIPT_FOLDER) if f.endswith(".txt")]
    output = {}

    for f in files:
        session_id = f.replace(".txt", "")
        res = build_index_for_session(session_id)
        output[session_id] = res

    return {"status": "ok", "data": output}


# ----------------------------
# SEARCH FUNCTION
# ----------------------------
def search(query, top_k=5, min_score=0.35):
    index = load_index()
    docs = index["documents"]

    if not docs:
        return {"hits": []}

    q_vec = embedder.encode([query])[0].reshape(1, -1)
    all_emb = np.array([d["embedding"] for d in docs])

    scores = cosine_similarity(q_vec, all_emb)[0]
    sorted_idx = np.argsort(scores)[::-1]

    hits = []
    for idx in sorted_idx:
        if scores[idx] < min_score:
            continue

        d = docs[idx]
        hits.append({
            "chunk": d["chunk"],
            "meta": {
                "session_id": d["session_id"],
                "chunk_id": d["chunk_id"]
            },
            "score": float(scores[idx])
        })

        if len(hits) == top_k:
            break

    return {"hits": hits}


# ----------------------------
# RAG ANSWER GENERATOR
# ----------------------------
def rag_ask(question, top_k=5):
    hits = search(question, top_k)["hits"]

    if not hits:
        return "The answer is not available in the provided transcripts."

    context = "\n\n".join([h["chunk"] for h in hits])

    if len(context.strip()) < 20:
        return "The answer is not available in the provided transcripts."

    # ⭐ UPDATED SIMPLE, CONTROLLED PROMPT
    prompt = f"""
You are a STRICT RAG assistant. Your job is to answer questions in simple, clear English.

CONTEXT MAY INCLUDE:
- Hindi, English, or Hinglish.
- Translate any Hindi or Hinglish into natural English before answering.

ANSWER RULES:
1. Use ONLY the information provided in the CONTEXT.
2. Your answer must be:
   - 2 to 4 sentences
   - Simple English
   - Natural and neutral tone
   - No meta commentary
3. Do NOT say:
   - "According to the context"
   - "According to the transcript"
   - "Based on the provided information"
4. Do NOT add assumptions or outside knowledge.
5. If the context does NOT contain the answer, reply EXACTLY:
   "The answer is not available in the provided transcripts."

CONTEXT:
{context}

QUESTION:
{question}

FINAL ANSWER (simple English only):
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Follow the RAG rules strictly. Answer only with simple English sentences, using context only."
                },
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"LLM Error: {str(e)}"
