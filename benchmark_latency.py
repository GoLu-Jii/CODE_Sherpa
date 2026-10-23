#!/usr/bin/env python3
"""
benchmark_latency.py

Runs the full CODE Sherpa query pipeline end-to-end on 20 realistic queries:
1. Retrieval via GraphRetriever (AST exact matching + semantic fallback + graph traversal)
2. Prompt generation with Mermaid graph and AST chunks
3. Inference via OpenRouter LLM
4. Citation extraction and response formatting

Measures and reports:
- Number of queries
- Per-query latency
- Average latency
- Median latency
- p95 latency
"""

import os
import sys
import time
import math
import statistics
from pathlib import Path

import dotenv
import chromadb

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
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
from app.generation.chat import generate_answer


def calculate_p95(values):
    """Calculates the 95th percentile using nearest-rank method."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = math.ceil(0.95 * len(sorted_values)) - 1
    return sorted_values[max(0, min(k, len(sorted_values) - 1))]


def run_latency_benchmark(num_queries: int = 20):
    queries_file = ROOT_DIR / "queries.txt"
    if not queries_file.exists():
        print(f"Error: {queries_file} not found.")
        sys.exit(1)

    all_queries = [line.strip() for line in queries_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected_queries = all_queries[:num_queries]

    print(f"============================================================")
    print(f"CODE SHERPA END-TO-END PIPELINE LATENCY BENCHMARK")
    print(f"============================================================")
    print(f"Loaded {len(selected_queries)} queries for benchmarking.\n")

    # Connect to Chroma
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "chroma_data")
    local_chroma_path = ROOT_DIR / persist_dir
    print(f"Connecting to Chroma database at: {local_chroma_path} ...")
    client = chromadb.PersistentClient(path=str(local_chroma_path))
    collection = client.get_collection("codesherpa_real_repo")
    print(f"Collection loaded ({collection.count()} chunks).\n")

    retriever = GraphRetriever(type("DB", (), {"collection": collection}))

    latencies = []
    retrieval_latencies = []
    pure_llm_latencies = []
    wait_latencies = []

    print(f"{'#':<3} | {'Query':<42} | {'Retrieval':<9} | {'Groq Infer':<10} | {'Rate Cooldown':<13} | {'Total (s)':<9}")
    print("-" * 95)

    for i, query in enumerate(selected_queries, 1):
        t0 = time.perf_counter()

        # Step 1: Retrieval
        t_ret_start = time.perf_counter()
        retrieved_data = retriever.retrieve_with_graph_context(query=query, n_results=4)
        t_ret_end = time.perf_counter()
        retrieval_time = t_ret_end - t_ret_start

        # Step 2: Generation (Prompt construction + LLM call + citation extraction)
        result = generate_answer(query=query, retrieved_chunk=retrieved_data)
        total_time = time.perf_counter() - t0

        timing = result.get("timing", {})
        pure_llm = timing.get("pure_inference_seconds", max(0.0, total_time - retrieval_time))
        rate_wait = timing.get("wait_seconds", 0.0)

        latencies.append(total_time)
        retrieval_latencies.append(retrieval_time)
        pure_llm_latencies.append(pure_llm)
        wait_latencies.append(rate_wait)

        q_disp = query if len(query) <= 42 else query[:39] + "..."
        print(f"{i:<3} | {q_disp:<42} | {retrieval_time:>7.3f}s | {pure_llm:>8.3f}s | {rate_wait:>11.3f}s | {total_time:>7.3f}s")

    avg_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    p95_latency = calculate_p95(latencies)

    avg_pure_llm = statistics.mean(pure_llm_latencies)
    median_pure_llm = statistics.median(pure_llm_latencies)
    p95_pure_llm = calculate_p95(pure_llm_latencies)

    avg_retrieval = statistics.mean(retrieval_latencies)
    avg_wait = statistics.mean(wait_latencies)

    print("-" * 95)
    print("\nBENCHMARK RESULTS SUMMARY (GROQ LLM):")
    print(f"Number of Queries:                 {len(latencies)}")
    print(f"Total End-to-End Average Latency:  {avg_latency:.4f} seconds")
    print(f"Total End-to-End Median Latency:   {median_latency:.4f} seconds")
    print(f"Total End-to-End p95 Latency:      {p95_latency:.4f} seconds")
    print("-" * 55)
    print(f"  -> Avg Retrieval Time:           {avg_retrieval:.4f} seconds")
    print(f"  -> Avg Pure Groq Inference Time: {avg_pure_llm:.4f} seconds  (Median: {median_pure_llm:.4f}s, p95: {p95_pure_llm:.4f}s)")
    print(f"  -> Avg Free-Tier Cooldown Wait:  {avg_wait:.4f} seconds")
    print("============================================================\n")


if __name__ == "__main__":
    run_latency_benchmark(20)
