# Easy Analyzer 🎧📄



Easy Analyzer is an AI-powered system that converts **live meetings or uploaded videos** into:

- Structured analysis reports

- Clean lecture-style notes

- Searchable knowledge using **RAG (Retrieval-Augmented Generation)**



The project demonstrates real-world usage of **LLMs, speech-to-text, embeddings, WebSockets, and secure API handling**.



---



## 🚀 Core Features



### 🔴 Live Meeting Capture

- Records live system audio using the browser

- Streams audio chunks via WebSocket

- Converts audio to text using **Groq Whisper**

- Generates:

&nbsp; - Analysis PDF

&nbsp; - Notes PDF

- Automatically indexes the session for RAG



---



### 🎥 Video Upload \& Analysis

- Upload recorded video files

- Extracts audio using **FFmpeg**

- Transcribes speech to text

- Generates:

&nbsp; - Analysis report

&nbsp; - Notes report

- Builds RAG index automatically



---



### 🔍 RAG (Retrieval-Augmented Generation)

- Searches across all transcripts

- Supports **English, Hindi, and Hinglish**

- Uses multilingual embeddings

- Answers questions **strictly from transcript data**

- No hallucinations or external knowledge



---



### 📄 PDF Generation

- Structured analysis PDF

- Structured notes PDF

- UTF-8 safe (supports Hindi text)

- Downloadable from frontend UI



---



## 🛠️ Tech Stack



### Backend

- Python

- FastAPI

- WebSockets

- Groq API

&nbsp; - Whisper (`whisper-large-v3`)

&nbsp; - LLMs (`qwen/qwen3-32b`, `llama-3.1-8b-instant`)

- FFmpeg (audio extraction)

- Sentence Transformers (multilingual embeddings)

- Scikit-learn (cosine similarity)



### Frontend

- HTML
- JavaScript

- React (via CDN)

- Tailwind CSS



### AI / NLP

- Speech-to-Text (Whisper)

- Transcript Analysis (LLM)

- Note Generation (LLM)

- RAG with vector search



---



## ⚙️ Setup Instructions

### 1️⃣ Clone Repository
git clone https://github.com/Vighnesh1607/Easy_Analyzer.git

## 2️⃣ Create Virtual Environment (recommended)

## 3️⃣ Install Dependencies
pip install -r requirements.txt

## 4️⃣ Configure API Key
GROQ_API_KEY=your_real_api_key_here

## 5️⃣ Run Backend Server
python STT/live_server.py

## 6️⃣ Run Frontend
Frontend/index.html










