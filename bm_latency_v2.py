#!/usr/bin/env python3
"""
bm_latency_v2.py
----------------
End-to-end latency benchmark for CODE Sherpa.

Runs 20 queries through the full pipeline (retrieval + prompt + LLM)
TWICE -- once with OpenRouter, once with Groq.

Design rules:
  - Identical prompt is built once per query, then sent to BOTH providers.
  - Provider order ALTERNATES per query (odd queries: OpenRouter first;
    even queries: Groq first) to neutralise warm-cache effects.
  - Retrieval time is measured once (same result reused for both providers).
  - LLM generation time is measured separately for each provider.
  - Failures are counted and recorded; a failed query does NOT crash the run.
  - API keys are NEVER printed or logged.
  - Does NOT modify any file in backend/ or .env.
  - Uses the same Chroma store as production (chroma_data/).
  - Writes bm_latency_v2.csv with per-query results.

Metrics reported per provider:
  - Exact model ID used (from .env)
  - Average, Median, p95, and failure count for:
      * retrieval latency  (shared, reported once)
      * LLM inference time
      * total end-to-end time
"""

import csv
import math
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import dotenv
import chromadb

# UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

dotenv.load_dotenv(ROOT_DIR / ".env")

from app.engine_rag.retriever import GraphRetriever
from app.generation.chat import (
    generate_mermaid_graph,
    format_graph_chunks,
    get_groq_client,
    get_openrouter_client,
)
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt


# ── Percentile helper ─────────────────────────────────────────────────────────
def p95(values: List[float]) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    k = math.ceil(0.95 * len(s)) - 1
    return s[max(0, min(k, len(s) - 1))]


# ── Prompt builder (identical to production generate_answer, minus the LLM call) ─
def build_messages(query: str, retrieved_data: Dict[str, Any]) -> List[Dict[str, str]]:
    mermaid = generate_mermaid_graph(retrieved_data)
    chunks = format_graph_chunks(retrieved_data)
    context = (
        f"Graph Structure (Mermaid):\n```mermaid\n{mermaid}\n```\n\nCode Chunks:\n{chunks}"
        if mermaid else chunks
    )
    user_prompt = build_user_prompt(query, context)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


# ── Single LLM call with timing ───────────────────────────────────────────────
def call_groq(messages: List[Dict[str, str]], model: str) -> Tuple[float, bool, str]:
    """Returns (duration_s, success, error_msg)."""
    client = get_groq_client()
    max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "600"))
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=max_tokens,
        )
        dur = time.perf_counter() - t0
        _ = resp.choices[0].message.content  # ensure response is consumed
        return dur, True, ""
    except Exception as exc:
        dur = time.perf_counter() - t0
        return dur, False, str(exc)[:120]


def call_openrouter(messages: List[Dict[str, str]], model: str) -> Tuple[float, bool, str]:
    """Returns (duration_s, success, error_msg)."""
    client = get_openrouter_client()
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=600,
        )
        dur = time.perf_counter() - t0
        _ = resp.choices[0].message.content
        return dur, True, ""
    except Exception as exc:
        dur = time.perf_counter() - t0
        return dur, False, str(exc)[:120]


# ── Main ──────────────────────────────────────────────────────────────────────
def run(num_queries: int = 20):
    queries_file = ROOT_DIR / "queries.txt"
    if not queries_file.exists():
        print(f"ERROR: {queries_file} not found.", file=sys.stderr)
        sys.exit(1)

    all_queries = [l.strip() for l in queries_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    queries = all_queries[:num_queries]

    groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    or_model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

    print("=" * 70)
    print("CODE SHERPA  --  END-TO-END LATENCY BENCHMARK  (v2)")
    print("=" * 70)
    print(f"Queries        : {len(queries)}")
    print(f"Groq model     : {groq_model}")
    print(f"OpenRouter model: {or_model}")

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "chroma_data")
    chroma_path = ROOT_DIR / persist_dir
    print(f"Chroma store   : {chroma_path}  (CHROMA_LOCAL={os.getenv('CHROMA_LOCAL')})")
    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection("codesherpa_real_repo")
    print(f"Collection     : codesherpa_real_repo  ({collection.count()} chunks)\n")

    retriever = GraphRetriever(type("DB", (), {"collection": collection})())

    # per-query result rows
    rows = []

    # per-provider timing lists (successes only for stats)
    groq_llm_times: List[float] = []
    or_llm_times: List[float] = []
    retrieval_times: List[float] = []
    groq_failures = 0
    or_failures = 0

    hdr = (
        f"{'#':>3}  {'Query':<38}  {'1st':^5}  "
        f"{'Retrieval':>9}  {'Groq':>8}  {'OR':>8}  "
        f"{'G-ok':^5}  {'OR-ok':^5}"
    )
    print(hdr)
    print("-" * len(hdr))

    for i, query in enumerate(queries, 1):
        # --- retrieval (done once, shared) ---
        t_ret = time.perf_counter()
        retrieved = retriever.retrieve_with_graph_context(query=query, n_results=4)
        retrieval_time = time.perf_counter() - t_ret
        retrieval_times.append(retrieval_time)

        # --- build identical prompt ---
        if retrieved.get("primary_nodes"):
            messages = build_messages(query, retrieved)
        else:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "I could not find relevant code in the repository to answer this query."},
            ]

        # --- alternating order ---
        # odd query index -> OpenRouter first; even -> Groq first
        first_provider = "openrouter" if i % 2 == 1 else "groq"

        if first_provider == "openrouter":
            or_time, or_ok, or_err = call_openrouter(messages, or_model)
            groq_time, groq_ok, groq_err = call_groq(messages, groq_model)
        else:
            groq_time, groq_ok, groq_err = call_groq(messages, groq_model)
            or_time, or_ok, or_err = call_openrouter(messages, or_model)

        if groq_ok:
            groq_llm_times.append(groq_time)
        else:
            groq_failures += 1

        if or_ok:
            or_llm_times.append(or_time)
        else:
            or_failures += 1

        q_disp = query if len(query) <= 38 else query[:35] + "..."
        print(
            f"{i:>3}  {q_disp:<38}  {first_provider[:2]:^5}  "
            f"{retrieval_time:>7.3f}s  {groq_time:>6.3f}s  {or_time:>6.3f}s  "
            f"{'Y' if groq_ok else 'N':^5}  {'Y' if or_ok else 'N':^5}"
        )
        if not groq_ok:
            print(f"     [GROQ ERROR] {groq_err}")
        if not or_ok:
            print(f"     [OR   ERROR] {or_err}")

        rows.append({
            "idx": i,
            "query": query,
            "first_provider": first_provider,
            "retrieval_s": round(retrieval_time, 4),
            "groq_llm_s": round(groq_time, 4),
            "groq_ok": groq_ok,
            "groq_error": groq_err,
            "or_llm_s": round(or_time, 4),
            "or_ok": or_ok,
            "or_error": or_err,
        })

    print("-" * len(hdr))

    # ── Summary ───────────────────────────────────────────────────────────────
    def fmt(lst):
        if not lst:
            return "   N/A   "
        return f"{statistics.mean(lst):.3f}s / {statistics.median(lst):.3f}s / {p95(lst):.3f}s"

    print(f"\n{'='*70}")
    print("RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"  Groq model      : {groq_model}")
    print(f"  OpenRouter model: {or_model}")
    print(f"\n  {'Metric':<28}  {'Groq':^26}  {'OpenRouter':^26}")
    print(f"  {'-'*28}  {'-'*26}  {'-'*26}")

    avg_ret = statistics.mean(retrieval_times) if retrieval_times else float("nan")
    med_ret = statistics.median(retrieval_times) if retrieval_times else float("nan")
    p95_ret = p95(retrieval_times) if retrieval_times else float("nan")

    print(f"  {'Retrieval avg/med/p95':<28}  {avg_ret:.3f}s / {med_ret:.3f}s / {p95_ret:.3f}s  (shared)")

    print(f"  {'LLM avg/med/p95':<28}  {fmt(groq_llm_times):<26}  {fmt(or_llm_times):<26}")

    g_total = [rows[j]["retrieval_s"] + rows[j]["groq_llm_s"] for j in range(len(rows)) if rows[j]["groq_ok"]]
    o_total = [rows[j]["retrieval_s"] + rows[j]["or_llm_s"] for j in range(len(rows)) if rows[j]["or_ok"]]
    print(f"  {'Total avg/med/p95':<28}  {fmt(g_total):<26}  {fmt(o_total):<26}")

    print(f"\n  Groq failures     : {groq_failures} / {len(queries)}")
    print(f"  OpenRouter failures: {or_failures} / {len(queries)}")
    print(f"  Alternating order  : odd queries -> OpenRouter first; even -> Groq first")

    # ── CSV ───────────────────────────────────────────────────────────────────
    csv_out = ROOT_DIR / "bm_latency_v2.csv"
    fieldnames = [
        "idx", "query", "first_provider",
        "retrieval_s",
        "groq_llm_s", "groq_ok", "groq_error",
        "or_llm_s", "or_ok", "or_error",
    ]
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nDetailed results written to: {csv_out.name}")
    print("=" * 70)


if __name__ == "__main__":
    run(20)
