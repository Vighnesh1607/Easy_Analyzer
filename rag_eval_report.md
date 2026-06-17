# RAG Evaluation Report — Easy Analyzer

**Date:** 2026-06-17 17:59:36  
**Model (embedding):** paraphrase-multilingual-MiniLM-L12-v2  
**Model (LLM):** llama-3.1-8b-instant  
**Total chunks indexed:** 3  
**Chunk size:** 120 words, overlap=20  

---

## 📊 Summary Metrics

| Metric | Score |
|---|---|
| Overall Accuracy | **90%** (9/10) |
| Hit Rate @ 5 (positive tests) | **88%** |
| Mean Reciprocal Rank (MRR) | **0.875** |
| Avg Cosine Score | **0.335** |
| Not-Available Rate (negative tests) | **100%** |
| Avg Retrieval Latency | **78 ms** |
| Avg Generation Latency | **623 ms** |

### Hit Rate by Language

| Language | Hit Rate | Num Tests |
|---|---|---|
| EN | 86% | 7 |
| HI | 100% | 1 |

---

## 📋 Per-Question Results

| ID | Lang | Question | Hits | Avg Cos | MRR | Correct? |
|---|---|---|---|---|---|---|
| Q1 | EN | What tools were discussed for building LLM applications... | 2 | 0.481 | 1.000 | ✅ |
| Q2 | EN | What is the course primarily about? | 1 | 0.354 | 1.000 | ✅ |
| Q3 | EN | What is Langsmith used for? | 1 | 0.314 | 1.000 | ✅ |
| Q4 | EN | Can someone build LLM apps without writing code? | 2 | 0.554 | 1.000 | ✅ |
| Q5 | HI | कोर्स में कौन से tools बताए गए हैं? | 2 | 0.405 | 1.000 | ✅ |
| Q6 | EN | What was mentioned about BJP? | 1 | 0.645 | 1.000 | ✅ |
| Q7 | EN | What is being distributed or promoted for free? | 1 | 0.186 | 0.000 | ❌ |
| Q8 | EN | What was said about distribution being strong? | 1 | 0.257 | 1.000 | ✅ |
| Q9 | EN | Who is the CEO of the company? | 0 | 0.000 | 0.000 | ✅ |
| Q10 | EN | What was the total budget discussed in the meeting? | 1 | 0.158 | 0.000 | ✅ |

---

## 💬 LLM Answers (Manual Faithfulness Review)

> Rate each answer 1–5: **5** = perfectly faithful, **1** = hallucinated

### Q1 ✅

**Q:** What tools were discussed for building LLM applications?  
**Hits:** 2 | **Avg Cosine:** 0.481 | **MRR:** 1.000  

**Answer:**
> Langraph, Crew AI, Agno, Langsmith were discussed as tools for building LLM applications. We were also taught many no-code tools like N at N. These tools help build LLM-based applications without writing code.

**Faithfulness score (fill in):** ___/5  

---

### Q2 ✅

**Q:** What is the course primarily about?  
**Hits:** 1 | **Avg Cosine:** 0.354 | **MRR:** 1.000  

**Answer:**
> The course is about building and creating LLM applications. It helps you learn to work with agents, frameworks, and tools like Langraph and Langsmith. The course also covers no-code tools for creating LLM applications.

**Faithfulness score (fill in):** ___/5  

---

### Q3 ✅

**Q:** What is Langsmith used for?  
**Hits:** 1 | **Avg Cosine:** 0.314 | **MRR:** 1.000  

**Answer:**
> Langsmith tool is used for. Langsmith is used for the operations of Large Language Models (LLM). We have taught you about Langraph, Crew AI, Agno, and many more.

**Faithfulness score (fill in):** ___/5  

---

### Q4 ✅

**Q:** Can someone build LLM apps without writing code?  
**Hits:** 2 | **Avg Cosine:** 0.554 | **MRR:** 1.000  

**Answer:**
> You can build LLM apps without writing code. This is possible with no-code tools. Many tools and frameworks are used for this purpose.

**Faithfulness score (fill in):** ___/5  

---

### Q5 ✅

**Q:** कोर्स में कौन से tools बताए गए हैं?  
**Hits:** 2 | **Avg Cosine:** 0.405 | **MRR:** 1.000  

**Answer:**
> In the course, Langraph, Crew AI, Agno, and Langsmith are mentioned as tools. Also, no-code tools like N at N are discussed.

**Faithfulness score (fill in):** ___/5  

---

### Q6 ✅

**Q:** What was mentioned about BJP?  
**Hits:** 1 | **Avg Cosine:** 0.645 | **MRR:** 1.000  

**Answer:**
> BJP got Bengal. BJP had a big celebration when they won the election. They gave free Jhal Muri to people as a part of the celebration.

**Faithfulness score (fill in):** ___/5  

---

### Q7 ❌

**Q:** What is being distributed or promoted for free?  
**Hits:** 1 | **Avg Cosine:** 0.186 | **MRR:** 0.000  

**Answer:**
> We have given you some courses for free. We have taught you about Langsmith and prompt engineering. No code tools are also being given to you for free.

**Faithfulness score (fill in):** ___/5  

---

### Q8 ✅

**Q:** What was said about distribution being strong?  
**Hits:** 1 | **Avg Cosine:** 0.257 | **MRR:** 1.000  

**Answer:**
> Distribution was so strong that next few days, packets reached all over India and the whole country, not just Bengal.

Distribution was very strong.

Packets reached all over India, a few days after.

**Faithfulness score (fill in):** ___/5  

---

### Q9 ✅ *(negative test)*

**Q:** Who is the CEO of the company?  
**Hits:** 0 | **Avg Cosine:** 0.000 | **MRR:** 0.000  

**Answer:**
> The answer is not available in the provided transcripts.

**Faithfulness score (fill in):** ___/5  

---

### Q10 ✅ *(negative test)*

**Q:** What was the total budget discussed in the meeting?  
**Hits:** 1 | **Avg Cosine:** 0.158 | **MRR:** 0.000  

**Answer:**
> The total budget is not discussed in the meeting. No specific budget is mentioned. The answer is not available in the provided transcripts.

**Faithfulness score (fill in):** ___/5  

---

## 🔧 Bugs Fixed Before This Eval

1. **Chunk overlap added** — 20-word overlap prevents boundary context loss
2. **Index deduplication** — Re-indexing replaces instead of appending
3. **Dynamic cosine threshold** — Replaces hardcoded 0.35 cutoff

## 🚀 Recommended Next Steps

- ⚠️  Low average cosine scores — check for encoding/garbling issues in transcripts
- Consider FAISS or ChromaDB for faster retrieval at scale
