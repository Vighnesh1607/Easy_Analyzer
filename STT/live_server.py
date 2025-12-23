# live_server.py
import os
import json
import uuid
import time
import ffmpeg
from fastapi import FastAPI, WebSocket, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq

import nlp_analyzer
import nlp_notes
from report_generator import generate_pdf
from report_notes_generator import generate_notes_pdf
import rag_engine

# -------------------------------------------------------
# PATHS
# -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LIVE_TRANSCRIPTS = os.path.join(BASE_DIR, "live_transcripts")
TRANSCRIPT_FOLDER = os.path.join(BASE_DIR, "transcripts")
ANALYSIS_FOLDER = os.path.join(BASE_DIR, "analysis")
ANALYSIS_NOTES = os.path.join(BASE_DIR, "analysis_notes")
LIVE_REPORTS = os.path.join(BASE_DIR, "live_reports")

for d in [LIVE_TRANSCRIPTS, TRANSCRIPT_FOLDER, ANALYSIS_FOLDER, ANALYSIS_NOTES, LIVE_REPORTS]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------
# FASTAPI SETUP
# -------------------------------------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------
def whisper_transcribe(wav_path):
    """Transcribe using Groq/Whisper model and return text (UTF-8)."""
    with open(wav_path, "rb") as f:
        res = client.audio.transcriptions.create(
            file=f,
            model="whisper-large-v3",
            response_format="verbose_json"
        )

    try:
        data = res.model_dump()
    except:
        data = res

    return data.get("text", "")


# -------------------------------------------------------
# WEBSOCKET LIVE TRANSCRIPTION (with RAG auto-index)
# -------------------------------------------------------
@app.websocket("/ws/live/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    raw_path = os.path.join(LIVE_TRANSCRIPTS, session_id + ".webm")
    wav_path = os.path.join(LIVE_TRANSCRIPTS, session_id + ".wav")
    txt_path = os.path.join(TRANSCRIPT_FOLDER, session_id + ".txt")

    # cleanup old files
    for p in [raw_path, wav_path, txt_path]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass

    selected_output = "analysis"  # default

    try:
        # Receive binary chunks / text markers
        while True:
            msg = await websocket.receive()

            # Text messages
            if "text" in msg and msg["text"]:
                text = msg["text"]

                if text.startswith("__OUTPUT_TYPE__::"):
                    selected_output = text.split("::")[1].strip()
                    try:
                        await websocket.send_text(f"__ACK_OUTPUT__::{selected_output}")
                    except:
                        pass
                    continue

                if text == "__END_MEETING__":
                    # client finished sending audio
                    break

            # Binary chunks
            if "bytes" in msg and msg["bytes"]:
                try:
                    with open(raw_path, "ab") as fh:
                        fh.write(msg["bytes"])
                except Exception as e:
                    # continue receiving; we'll log and continue
                    print("Failed to write chunk:", e)
                continue

        # small wait to ensure disk flush
        time.sleep(0.3)

        # convert WebM -> WAV (mono 16k)
        try:
            ffmpeg.input(raw_path).output(wav_path, ac=1, ar=16000).overwrite_output().run(quiet=True)
        except Exception as e:
            # conversion failed
            try:
                await websocket.send_text(f"__ERROR_FINAL__::FFMPEG conversion failed: {str(e)}")
            except:
                pass
            return

        # Transcribe (Whisper)
        transcript = ""
        try:
            transcript = whisper_transcribe(wav_path)
        except Exception as e:
            try:
                await websocket.send_text(f"__ERROR_FINAL__::Transcription failed: {str(e)}")
            except:
                pass
            return

        # Save transcript (UTF-8)
        try:
            with open(txt_path, "w", encoding="utf-8", errors="ignore") as fh:
                fh.write(transcript)
        except Exception as e:
            print("Failed to save transcript:", e)

        # ANALYSIS
        try:
            rawA = nlp_analyzer.analyze_transcript(transcript)
            cleanA = nlp_analyzer.clean_json_output(rawA)
            parsedA = nlp_analyzer.normalize_keys(json.loads(cleanA))

            with open(os.path.join(ANALYSIS_FOLDER, session_id + ".json"), "w", encoding="utf-8") as fh:
                json.dump(parsedA, fh, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Analysis error:", e)
            parsedA = {}

        # NOTES
        try:
            rawN = nlp_notes.analyze_notes(transcript)
            cleanN = nlp_analyzer.clean_json_output(rawN)
            parsedN = json.loads(cleanN)

            with open(os.path.join(ANALYSIS_NOTES, session_id + ".json"), "w", encoding="utf-8") as fh:
                json.dump(parsedN, fh, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Notes error:", e)
            parsedN = {}

        # Generate PDFs (if data exists)
        try:
            if selected_output in ["analysis", "both"]:
                generate_pdf(parsedA, os.path.join(LIVE_REPORTS, session_id + "_analysis.pdf"))
            if selected_output in ["notes", "both"]:
                generate_notes_pdf(parsedN, os.path.join(LIVE_REPORTS, session_id + "_notes.pdf"))
        except Exception as e:
            print("PDF generation error:", e)

        # ---------- AUTO-BUILD RAG INDEX FOR LIVE SESSION ----------
        try:
            # Build index for this session so RAG can answer immediately
            rag_engine.build_index_for_session(session_id)
            try:
                await websocket.send_text(f"__RAG_INDEXED__::{session_id}")
            except:
                pass
            print(f"[RAG] Indexed live session: {session_id}")
        except Exception as e:
            print("[RAG] Index build error for live session:", e)
            try:
                await websocket.send_text(f"__RAG_INDEX_ERROR__::{str(e)}")
            except:
                pass

        # Notify client PDFs are ready (keeps existing behavior)
        try:
            await websocket.send_text(f"__REPORT_READY__::{session_id}")
        except:
            pass

    except Exception as e:
        # Try to notify client of final error; ignore if socket closed
        try:
            await websocket.send_text(f"__ERROR_FINAL__::{str(e)}")
        except:
            pass
        print("WebSocket handler error:", e)
    finally:
        try:
            await websocket.close()
        except:
            pass


# -------------------------------------------------------
# UPLOAD VIDEO (UTF-8 safe + auto-index)
# -------------------------------------------------------
@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...), output_type: str = Form(...)):
    try:
        vid = "video_" + str(uuid.uuid4())
        video_path = os.path.join(LIVE_TRANSCRIPTS, vid + ".mp4")
        wav_path = os.path.join(LIVE_TRANSCRIPTS, vid + ".wav")

        # Save uploaded video (raw bytes)
        with open(video_path, "wb") as f:
            f.write(await file.read())

        # Convert to WAV
        try:
            ffmpeg.input(video_path).output(wav_path, ac=1, ar=16000).overwrite_output().run(quiet=True)
        except Exception as e:
            return {"error": f"FFMPEG conversion failed: {e}"}

        # Transcribe
        try:
            with open(wav_path, "rb") as audio:
                t = client.audio.transcriptions.create(
                    file=audio,
                    model="whisper-large-v3",
                    response_format="verbose_json"
                )
            try:
                transcript = t.model_dump().get("text", "")
            except:
                transcript = t.get("text", "")
        except Exception as e:
            return {"error": f"Transcription failed: {e}"}

        # Save transcript (UTF-8)
        try:
            with open(os.path.join(TRANSCRIPT_FOLDER, vid + ".txt"), "w", encoding="utf-8", errors="ignore") as fh:
                fh.write(transcript)
        except Exception as e:
            print("Failed to save transcript:", e)

        # ANALYSIS
        try:
            rawA = nlp_analyzer.analyze_transcript(transcript)
            cleanA = nlp_analyzer.clean_json_output(rawA)
            parsedA = nlp_analyzer.normalize_keys(json.loads(cleanA))
            with open(os.path.join(ANALYSIS_FOLDER, vid + ".json"), "w", encoding="utf-8") as fh:
                json.dump(parsedA, fh, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Analysis save error:", e)
            parsedA = {}

        # NOTES
        try:
            rawN = nlp_notes.analyze_notes(transcript)
            cleanN = nlp_analyzer.clean_json_output(rawN)
            parsedN = json.loads(cleanN)
            with open(os.path.join(ANALYSIS_NOTES, vid + ".json"), "w", encoding="utf-8") as fh:
                json.dump(parsedN, fh, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Notes save error:", e)
            parsedN = {}

        # Generate PDFs
        try:
            generate_pdf(parsedA, os.path.join(LIVE_REPORTS, vid + "_analysis.pdf"))
            generate_notes_pdf(parsedN, os.path.join(LIVE_REPORTS, vid + "_notes.pdf"))
        except Exception as e:
            print("PDF generation error:", e)

        # Build RAG index for this uploaded video (so it's searchable immediately)
        try:
            rag_engine.build_index_for_session(vid)
            print(f"[RAG] Indexed uploaded video: {vid}")
        except Exception as e:
            print("[RAG] Index build error for upload:", e)

        # Return both links + session id so frontend can index or store if needed
        return {
            "analysis": f"http://localhost:8000/live-report/{vid}_analysis",
            "notes": f"http://localhost:8000/live-report/{vid}_notes",
            "session_id": vid
        }

    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------------
# PDF FETCHER
# -------------------------------------------------------
@app.get("/live-report/{session_id}")
def get_live_report(session_id: str):
    candidates = [
        os.path.join(LIVE_REPORTS, session_id + ".pdf"),
        os.path.join(LIVE_REPORTS, session_id + "_analysis.pdf"),
        os.path.join(LIVE_REPORTS, session_id + "_notes.pdf"),
    ]

    for p in candidates:
        if os.path.exists(p):
            return FileResponse(p, media_type="application/pdf")

    return {"error": "PDF not found"}


# -------------------------------------------------------
# RAG ENDPOINTS (unchanged)
# -------------------------------------------------------
class RagQuery(BaseModel):
    question: str
    top_k: int = 5


@app.post("/rag/store_all")
def rag_store_all():
    try:
        result = rag_engine.build_index_from_all()
        return {"status": "ok", "data": result}
    except Exception as e:
        print("[RAG ERROR store_all]:", e)
        return {"error": str(e)}


@app.post("/rag/store/{session_id}")
def rag_store_one(session_id: str):
    try:
        result = rag_engine.build_index_for_session(session_id)
        return {"status": "ok", "data": result}
    except Exception as e:
        print("[RAG ERROR store_one]:", e)
        return {"error": str(e)}


@app.post("/rag/query")
def rag_query(data: RagQuery):
    try:
        search_result = rag_engine.search(data.question, data.top_k)
        answer = rag_engine.rag_ask(data.question, data.top_k)

        # ensure wrapper format for frontend compatibility
        results_wrapper = {"hits": search_result.get("hits", [])} if isinstance(search_result, dict) else search_result

        return {
            "results": results_wrapper,
            "answer": answer
        }
    except Exception as e:
        print("[RAG ERROR query]:", e)
        return {"error": str(e)}
