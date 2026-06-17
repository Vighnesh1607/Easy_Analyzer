# Easy Analyzer — Technical Interview Preparation Guide

This guide compiles all possible technical questions, answers, and implementation details for the **Easy Analyzer** project. You can use this document to revise and prepare for your interview.

---

## 🗺️ Section 1: System Architecture & Tech Stack

### Q1: What is the core functionality and purpose of Easy Analyzer?
* **Answer**: Easy Analyzer is an AI-powered meeting intelligence application. It enables users to either stream live audio from their browser (via screen/tab sharing) or upload video files. The system transcribes the speech, indices the transcript into a local RAG (Retrieval-Augmented Generation) system for semantic search, and compiles structured meeting minutes (summaries, decisions, action items, and keywords) into downloadable PDF reports.

### Q2: Break down the technology stack and the reason for choosing each component.
* **Answer**:
  * **Frontend**: Vanilla HTML5, CSS3, and pure JavaScript. Chosen to ensure instant loading times, bypass compile/bundling steps, and handle raw binary data streaming with zero framework overhead.
  * **Backend**: FastAPI (Python). Chosen for its high-performance asynchronous runtime, native WebSocket support, and automatically generated OpenAPI documentation.
  * **Speech-to-Text**: Groq Cloud's Whisper-large-v3 API. Chosen for its sub-second transcription speeds and highly accurate speech recognition.
  * **Embeddings**: SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`). Chosen to support local semantic indexing and cross-lingual English/Hindi search with low memory footprint (~117MB).
  * **LLM Reasoning**: Llama-3.1-8b-instant (via Groq). Chosen for fast, low-latency text summarizing and Q&A reasoning.
  * **PDF Generation**: ReportLab. Chosen for custom PDF layout building directly in Python.

---

## 🌐 Section 2: Frontend, Screen Capturing & WebSockets

### Q3: How is real-time screen share audio captured in the browser?
* **Answer**: It utilizes the browser's native **Screen Capture API**:
  ```javascript
  const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
  ```
  Once the user grants permission, we isolate the audio track from the stream and pipe it into a native **`MediaRecorder`** object.

### Q4: How is audio streamed to the backend in real time?
* **Answer**:
  * The `MediaRecorder` is configured to trigger a `ondataavailable` event every **250 milliseconds**, yielding a small chunk of raw WebM binary audio.
  * These raw blobs are pushed immediately over a **WebSocket** connection (`ws://localhost:8080/ws`) to the FastAPI backend.
  * The backend continuously appends these incoming audio chunks into an in-memory buffer, which is periodically sent to Groq's Whisper API to generate real-time transcript updates.

### Q5: Why WebSockets instead of HTTP POST requests?
* **Answer**: HTTP is a stateless request-response protocol. Establishing a new HTTP connection every 250ms would introduce massive TCP/TLS handshake latency and header bloat. WebSockets establish a single persistent, full-duplex TCP connection, allowing the client to stream binary packets with negligible overhead and receive real-time text updates concurrently.

---

## 🔍 Section 3: RAG (Retrieval-Augmented Generation) Pipeline

### Q6: How does the chunking strategy work, and why is "overlap" critical?
* **Answer**:
  * The transcript is split into text blocks of maximum **120 words**.
  * A sliding window of **20 words of overlap** is maintained between adjacent chunks.
  * **Why overlap is critical**: If a meeting participant mentions a critical point right at the split boundary, a naive chunker would divide the sentence across two chunks. This severing of context makes it impossible for either chunk to score highly during search. An overlap ensures the surrounding context remains intact for both chunks.

### Q7: Why did you choose the `paraphrase-multilingual-MiniLM-L12-v2` model for embeddings?
* **Answer**:
  * **Hinglish/Multilingual Support**: Real-world meetings in India often involve mixed language use (mixed Hindi and English, e.g. *"free का promotion"*). Standard English models cannot map these concepts together. This model is trained on a massive multilingual parallel corpus, allowing English search queries to match Devanagari or Hinglish transcript text.
  * **Resource Constraints**: At only 117MB, it fits easily in RAM and computes embeddings locally in milliseconds on standard CPUs, eliminating the cost and network latency of cloud embedding APIs (like OpenAI).

### Q8: How is the vector database implemented?
* **Answer**: We built a lightweight, local file-based vector index stored in **`STT/rag_index.json`**. It contains a list of documents where each record stores the raw chunk text, metadata, and the 384-dimensional embedding array. Cosine similarities are computed at query time using NumPy:
  ```python
  scores = cosine_similarity(query_vector, index_vectors)[0]
  ```

### Q9: Explain your dynamic thresholding logic and how it improves retrieval.
* **Answer**:
  * Naive RAG systems use a static cosine similarity cutoff (like `0.35`). This fails when average similarity scores are naturally low (yielding 0 results) or naturally high (admitting junk context).
  * We calculate a **dynamic threshold** for each search query:
    $$\text{Threshold} = \max(0.13, \text{mean}(\text{scores}) - 0.5 \times \text{std}(\text{scores}))$$
  * This dynamically scales the filter based on the distribution of similarities for that specific query, while keeping a safety floor of **`0.13`** to filter out completely irrelevant documents.

### Q10: How do you prevent LLM hallucinations when the answer isn't in the transcripts?
* **Answer**:
  * **Retriever Filter**: If no chunks score above the dynamic threshold, we pass an empty context to the LLM.
  * **Strict Prompt Engineering**: The LLM prompt instructs:
    ```
    You are a STRICT RAG assistant. Use ONLY the provided context.
    If the context does not contain the answer, reply EXACTLY:
    "The answer is not available in the provided transcripts."
    Do not add assumptions or outside knowledge.
    ```
  * In our evaluation tests, this zero-hallucination constraint achieved a **100% Not-Available success rate**.

---

## 🛠️ Section 4: Key Bug Fixes & Troubleshooting

### Q11: How did you fix the RAG session deduplication bug?
* **Answer**: Re-indexing a session previously appended duplicate chunks to `rag_index.json` because the script did not check for pre-existing records. This caused index bloat and duplicate text in the prompt context. The fix was introducing a deletion filter before encoding:
  ```python
  index["documents"] = [d for d in index["documents"] if d.get("session_id") != session_id]
  ```

### Q12: How did you address retrieval failures for cross-lingual Hinglish queries?
* **Answer**: In our evaluation suite, the query *"What is being distributed or promoted for free?"* matched a transcript chunk containing the Hinglish phrase *"free का promotion"* with a low cosine score of `0.138` (due to model size limitations). Since our original threshold floor was hardcoded at `0.25`, the correct chunk was filtered out. We resolved this by reducing the floor to `0.13`, which allowed the cross-lingual match to pass to Llama-3.1, which successfully translated and extracted the answer.

### Q13: What caused terminal crashes on Windows and how did you resolve it?
* **Answer**: The default output encoding of Windows terminals (usually CP1252) cannot encode Unicode characters like emojis (✅/❌) or Hindi scripts. Printing them caused a `UnicodeEncodeError`. We fixed this by forcing UTF-8 on Windows at the entry point of the python scripts:
  ```python
  import sys, io
  if sys.stdout.encoding != 'utf-8':
      sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
  ```

---

## 📈 Section 5: Key Metrics (from our Automated Evaluation)
* **Overall Accuracy**: **90%**
* **Hit Rate @ 5 (Positive Tests)**: **88%**
* **Mean Reciprocal Rank (MRR)**: **0.875**
* **Not-Available Rate (Hallucination Prevention)**: **100%**
* **Avg Retrieval Latency**: **~73 ms** (NumPy-based search)
* **Avg Generation Latency**: **~799 ms** (Llama-3.1-8b API)
