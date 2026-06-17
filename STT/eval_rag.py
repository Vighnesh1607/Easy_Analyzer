"""
eval_rag.py — Automated RAG System Evaluation for Easy Analyzer
================================================================
Runs a test suite of questions against the RAG engine and produces:
  - Per-question retrieval scores (cosine similarity, hit presence)
  - LLM answers for manual faithfulness review
  - Summary metrics (hit rate, MRR, avg score, not-available rate)
  - Outputs: rag_eval_report.md

Usage:
    cd STT
    python eval_rag.py
"""

import os
import sys
import io
import json
import time
import datetime
import numpy as np
from dotenv import load_dotenv

# Force UTF-8 for stdout and stderr to avoid Windows cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

# Make sure we can import rag_engine from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rag_engine

# ─────────────────────────────────────────────
# TEST SUITE
# ─────────────────────────────────────────────
# Each entry:
#   question        : the query to test
#   keywords        : list of strings that SHOULD appear in retrieved chunks
#                     (used for hit-rate scoring — case-insensitive)
#   expect_no_answer: True if the correct LLM response is "not available"
#   lang            : "en" | "hi" | "hinglish"

TEST_CASES = [
    # ── Transcript 1: LLM Applications Course (Hinglish) ──────────────────
    {
        "id": "Q1",
        "question": "What tools were discussed for building LLM applications?",
        "keywords": ["langraph", "crew", "agno", "n8n", "no code"],
        "expect_no_answer": False,
        "lang": "en",
    },
    {
        "id": "Q2",
        "question": "What is the course primarily about?",
        "keywords": ["llm", "application", "course"],
        "expect_no_answer": False,
        "lang": "en",
    },
    {
        "id": "Q3",
        "question": "What is Langsmith used for?",
        "keywords": ["langsmith", "llm ops", "prompt engineering"],
        "expect_no_answer": False,
        "lang": "en",
    },
    {
        "id": "Q4",
        "question": "Can someone build LLM apps without writing code?",
        "keywords": ["no code", "without", "code"],
        "expect_no_answer": False,
        "lang": "en",
    },
    {
        "id": "Q5",
        "question": "कोर्स में कौन से tools बताए गए हैं?",   # Hindi: which tools were mentioned?
        "keywords": ["langraph", "crew", "agno"],
        "expect_no_answer": False,
        "lang": "hi",
    },

    # ── Transcript 2: Distribution / Elections (Hinglish) ─────────────────
    {
        "id": "Q6",
        "question": "What was mentioned about BJP?",
        "keywords": ["bjp", "election"],
        "expect_no_answer": False,
        "lang": "en",
    },
    {
        "id": "Q7",
        "question": "What is being distributed or promoted for free?",
        "keywords": ["free", "promotion"],
        "expect_no_answer": False,
        "lang": "en",
    },
    {
        "id": "Q8",
        "question": "What was said about distribution being strong?",
        "keywords": ["distribution", "strong", "packets"],
        "expect_no_answer": False,
        "lang": "en",
    },

    # ── Negative Tests: Should return "not available" ──────────────────────
    {
        "id": "Q9",
        "question": "Who is the CEO of the company?",
        "keywords": [],
        "expect_no_answer": True,
        "lang": "en",
    },
    {
        "id": "Q10",
        "question": "What was the total budget discussed in the meeting?",
        "keywords": [],
        "expect_no_answer": True,
        "lang": "en",
    },
]

NOT_AVAILABLE_PHRASE = "not available in the provided transcripts"


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def hit_check(hits, keywords):
    """Return True if any keyword appears in any retrieved chunk (case-insensitive)."""
    if not keywords:
        return None   # N/A for negative tests
    combined = " ".join(h["chunk"].lower() for h in hits)
    return any(kw.lower() in combined for kw in keywords)


def mrr_score(hits, keywords):
    """Mean Reciprocal Rank: 1/rank of first hit chunk containing a keyword."""
    if not keywords or not hits:
        return 0.0
    for rank, h in enumerate(hits, start=1):
        chunk_lower = h["chunk"].lower()
        if any(kw.lower() in chunk_lower for kw in keywords):
            return 1.0 / rank
    return 0.0


def avg_score(hits):
    if not hits:
        return 0.0
    return sum(h["score"] for h in hits) / len(hits)


def is_not_available(answer):
    return NOT_AVAILABLE_PHRASE.lower() in answer.lower()


# ─────────────────────────────────────────────
# MAIN EVALUATION
# ─────────────────────────────────────────────
def run_eval():
    print("\n" + "=" * 60)
    print("  Easy Analyzer — RAG Evaluation")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # First, rebuild the index with the fixed chunker
    print("\n[1/3] Re-building RAG index with fixed chunker (overlap=20)...")
    result = rag_engine.build_index_from_all()
    index = rag_engine.load_index()
    total_chunks = len(index["documents"])
    print(f"      Index ready: {total_chunks} chunks across {len(result.get('data', {}))} sessions")

    if total_chunks == 0:
        print("\n⚠  No transcripts found — please run at least one session first.")
        print("   Place .txt transcripts in STT/transcripts/ and re-run.")
        return

    results = []
    print(f"\n[2/3] Running {len(TEST_CASES)} test questions...\n")

    for tc in TEST_CASES:
        qid = tc["id"]
        question = tc["question"]
        print(f"  {qid}: {question[:70]}...")

        t0 = time.time()
        hits = rag_engine.search(question, top_k=5)["hits"]
        retrieval_ms = int((time.time() - t0) * 1000)

        t1 = time.time()
        answer = rag_engine.rag_ask(question, top_k=5)
        generation_ms = int((time.time() - t1) * 1000)

        hit = hit_check(hits, tc["keywords"])
        mrr = mrr_score(hits, tc["keywords"])
        avg = avg_score(hits)
        no_ans = is_not_available(answer)

        # For negative tests, "correct" means no_ans==True
        # For positive tests, "correct" means hit==True
        if tc["expect_no_answer"]:
            correct = no_ans
        else:
            correct = bool(hit)

        result = {
            "id": qid,
            "lang": tc["lang"],
            "question": question,
            "expect_no_answer": tc["expect_no_answer"],
            "num_hits": len(hits),
            "hit": hit,
            "mrr": round(mrr, 3),
            "avg_cosine": round(avg, 3),
            "retrieval_ms": retrieval_ms,
            "generation_ms": generation_ms,
            "answer": answer,
            "no_answer": no_ans,
            "correct": correct,
        }
        results.append(result)

        status = "✅" if correct else "❌"
        print(f"        {status}  hits={len(hits)}  avg_cos={avg:.3f}  mrr={mrr:.3f}  ({retrieval_ms}ms + {generation_ms}ms)")
        time.sleep(0.3)   # small pause to avoid rate limits

    # ─────────────────────────────────────────
    # COMPUTE SUMMARY METRICS
    # ─────────────────────────────────────────
    positive_tests = [r for r in results if not r["expect_no_answer"]]
    negative_tests = [r for r in results if r["expect_no_answer"]]

    hit_rate = sum(1 for r in positive_tests if r["hit"]) / max(len(positive_tests), 1)
    avg_mrr = np.mean([r["mrr"] for r in positive_tests]) if positive_tests else 0
    avg_cos = np.mean([r["avg_cosine"] for r in results]) if results else 0
    not_avail_rate = sum(1 for r in negative_tests if r["no_answer"]) / max(len(negative_tests), 1)
    overall_acc = sum(1 for r in results if r["correct"]) / max(len(results), 1)
    avg_retrieval_ms = np.mean([r["retrieval_ms"] for r in results])
    avg_generation_ms = np.mean([r["generation_ms"] for r in results])

    by_lang = {}
    for r in positive_tests:
        lang = r["lang"]
        by_lang.setdefault(lang, []).append(r)

    print("\n[3/3] Generating report...")

    # ─────────────────────────────────────────
    # WRITE MARKDOWN REPORT
    # ─────────────────────────────────────────
    report_path = os.path.join(os.path.dirname(__file__), "..", "rag_eval_report.md")
    report_path = os.path.abspath(report_path)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# RAG Evaluation Report — Easy Analyzer\n\n")
        f.write(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Model (embedding):** paraphrase-multilingual-MiniLM-L12-v2  \n")
        f.write(f"**Model (LLM):** llama-3.1-8b-instant  \n")
        f.write(f"**Total chunks indexed:** {total_chunks}  \n")
        f.write(f"**Chunk size:** 120 words, overlap=20  \n\n")
        f.write("---\n\n")

        f.write("## 📊 Summary Metrics\n\n")
        f.write("| Metric | Score |\n|---|---|\n")
        f.write(f"| Overall Accuracy | **{overall_acc:.0%}** ({sum(1 for r in results if r['correct'])}/{len(results)}) |\n")
        f.write(f"| Hit Rate @ 5 (positive tests) | **{hit_rate:.0%}** |\n")
        f.write(f"| Mean Reciprocal Rank (MRR) | **{avg_mrr:.3f}** |\n")
        f.write(f"| Avg Cosine Score | **{avg_cos:.3f}** |\n")
        f.write(f"| Not-Available Rate (negative tests) | **{not_avail_rate:.0%}** |\n")
        f.write(f"| Avg Retrieval Latency | **{avg_retrieval_ms:.0f} ms** |\n")
        f.write(f"| Avg Generation Latency | **{avg_generation_ms:.0f} ms** |\n\n")

        # By language
        if by_lang:
            f.write("### Hit Rate by Language\n\n")
            f.write("| Language | Hit Rate | Num Tests |\n|---|---|---|\n")
            for lang, lang_results in sorted(by_lang.items()):
                lr_hit = sum(1 for r in lang_results if r["hit"]) / max(len(lang_results), 1)
                f.write(f"| {lang.upper()} | {lr_hit:.0%} | {len(lang_results)} |\n")
            f.write("\n")

        f.write("---\n\n")
        f.write("## 📋 Per-Question Results\n\n")
        f.write("| ID | Lang | Question | Hits | Avg Cos | MRR | Correct? |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in results:
            ok = "✅" if r["correct"] else "❌"
            q_short = r["question"][:55] + ("..." if len(r["question"]) > 55 else "")
            f.write(f"| {r['id']} | {r['lang'].upper()} | {q_short} | {r['num_hits']} | {r['avg_cosine']:.3f} | {r['mrr']:.3f} | {ok} |\n")

        f.write("\n---\n\n")
        f.write("## 💬 LLM Answers (Manual Faithfulness Review)\n\n")
        f.write("> Rate each answer 1–5: **5** = perfectly faithful, **1** = hallucinated\n\n")

        for r in results:
            ok = "✅" if r["correct"] else "❌"
            neg = " *(negative test)*" if r["expect_no_answer"] else ""
            f.write(f"### {r['id']} {ok}{neg}\n\n")
            f.write(f"**Q:** {r['question']}  \n")
            f.write(f"**Hits:** {r['num_hits']} | **Avg Cosine:** {r['avg_cosine']:.3f} | **MRR:** {r['mrr']:.3f}  \n\n")
            f.write(f"**Answer:**\n> {r['answer']}\n\n")
            f.write(f"**Faithfulness score (fill in):** ___/5  \n\n")
            f.write("---\n\n")

        f.write("## 🔧 Bugs Fixed Before This Eval\n\n")
        f.write("1. **Chunk overlap added** — 20-word overlap prevents boundary context loss\n")
        f.write("2. **Index deduplication** — Re-indexing replaces instead of appending\n")
        f.write("3. **Dynamic cosine threshold** — Replaces hardcoded 0.35 cutoff\n\n")

        f.write("## 🚀 Recommended Next Steps\n\n")
        if hit_rate < 0.7:
            f.write("- ⚠️  Hit rate is below 70% — consider upgrading to `multilingual-e5-base` embeddings\n")
        if avg_mrr < 0.5:
            f.write("- ⚠️  MRR is low — add cross-encoder re-ranking stage\n")
        if not_avail_rate < 0.8:
            f.write("- ⚠️  LLM is hallucinating on negative tests — tighten the prompt\n")
        if avg_cos < 0.4:
            f.write("- ⚠️  Low average cosine scores — check for encoding/garbling issues in transcripts\n")
        f.write("- Consider FAISS or ChromaDB for faster retrieval at scale\n")

    print(f"\n{'='*60}")
    print(f"  ✅ Evaluation Complete")
    print(f"{'='*60}")
    print(f"\n  Overall Accuracy : {overall_acc:.0%}")
    print(f"  Hit Rate @ 5    : {hit_rate:.0%}")
    print(f"  MRR             : {avg_mrr:.3f}")
    print(f"  Avg Cosine      : {avg_cos:.3f}")
    print(f"  Not-Avail Rate  : {not_avail_rate:.0%}")
    print(f"\n  📄 Report saved to: {report_path}")
    print()

    return results


if __name__ == "__main__":
    run_eval()
