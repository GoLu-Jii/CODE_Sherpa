#!/usr/bin/env python3
"""
benchmark_tokens.py

Benchmarks prompt token consumption between:
1. CODE Sherpa: Exact AST chunks + Mermaid graph context
2. Baseline: Full contents of every file containing a retrieved chunk
"""

import os
import sys
import csv
import re
from pathlib import Path
from typing import Dict, Any, List, Set

import dotenv
import tiktoken
import chromadb

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Setup paths and environment
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

dotenv.load_dotenv(ROOT_DIR / ".env")

from app.engine_rag.retriever import GraphRetriever
from app.generation.chat import generate_mermaid_graph, format_graph_chunks
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt


def get_token_encoder():
    return tiktoken.get_encoding("cl100k_base")


def count_message_tokens(messages: List[Dict[str, str]], enc) -> int:
    """Accurately count tokens in chat completion message list."""
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # overhead per message: <im_start>{role}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(enc.encode(str(value)))
    num_tokens += 2  # overhead for assistant priming
    return num_tokens


def build_sherpa_prompt(query: str, retrieved_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Builds the exact message payload CODE Sherpa sends to the LLM."""
    if not retrieved_data.get("primary_nodes"):
        user_prompt = "I could not find relevant code in the repository to answer this query."
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    mermaid_graph = generate_mermaid_graph(retrieved_data)
    chunks_context = format_graph_chunks(retrieved_data)

    if mermaid_graph:
        context = f"Graph Structure (Mermaid):\n```mermaid\n{mermaid_graph}\n```\n\nCode Chunks:\n{chunks_context}"
    else:
        context = chunks_context

    user_prompt = build_user_prompt(query, context)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def extract_file_paths_for_chunks(retrieved_data: Dict[str, Any], collection) -> Set[str]:
    """Finds all unique source file paths containing the retrieved chunks."""
    all_nodes = retrieved_data.get("primary_nodes", []) + retrieved_data.get("downstream_context", [])
    file_paths = set()

    for node in all_nodes:
        nid = node.get("node_id")
        code = node.get("code", "")

        # 1. Try regex from code header if available (File: path/to/file.py)
        match = re.search(r"^File:\s*([^\r\n]+)", code, re.MULTILINE)
        if match:
            fp = match.group(1).strip()
            if fp:
                file_paths.add(fp)
                continue

        # 2. Try collection metadata lookup
        if nid and collection is not None:
            try:
                res = collection.get(ids=[nid], include=["metadatas"])
                if res and res.get("metadatas") and len(res["metadatas"]) > 0:
                    fp = res["metadatas"][0].get("file_path")
                    if fp:
                        file_paths.add(fp)
                        continue
            except Exception:
                pass

    return file_paths


def build_baseline_prompt(query: str, file_paths: Set[str], repo_root: Path) -> List[Dict[str, str]]:
    """Builds baseline prompt with FULL file contents of all files containing retrieved chunks."""
    if not file_paths:
        user_prompt = "I could not find relevant code in the repository to answer this query."
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    file_blocks = []
    for rel_path in sorted(file_paths):
        full_path = repo_root / rel_path
        if not full_path.exists():
            # Try looking inside backend/
            alt_path = repo_root / "backend" / rel_path
            if alt_path.exists():
                full_path = alt_path

        if full_path.exists() and full_path.is_file():
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                content = f"# Error reading file {rel_path}: {e}"
        else:
            content = f"# File not found on disk: {rel_path}"

        block = f"FILE: {rel_path}\n```python\n{content}\n```"
        file_blocks.append(block)

    baseline_context = "\n\n---\n\n".join(file_blocks)
    user_prompt = build_user_prompt(query, baseline_context)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def run_benchmark():
    queries_file = ROOT_DIR / "queries.txt"
    if not queries_file.exists():
        print(f"Error: {queries_file} not found.")
        sys.exit(1)

    queries = [line.strip() for line in queries_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(queries)} queries from {queries_file.name}\n")

    # Connect to Chroma
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "chroma_data")
    local_chroma_path = ROOT_DIR / persist_dir
    print(f"Connecting to Chroma database at: {local_chroma_path} ...")
    client = chromadb.PersistentClient(path=str(local_chroma_path))
    collection = client.get_collection("codesherpa_real_repo")
    print(f"Chroma collection 'codesherpa_real_repo' loaded with {collection.count()} chunks.\n")

    retriever = GraphRetriever(type("DB", (), {"collection": collection}))
    enc = get_token_encoder()

    results = []
    total_sherpa_tokens = 0
    total_baseline_tokens = 0

    print(f"{'#':<3} | {'Query':<45} | {'Sherpa':<8} | {'Baseline':<9} | {'Reduction':<10}")
    print("-" * 85)

    for i, query in enumerate(queries, 1):
        # 1. Run real retrieval pipeline up to LLM prompt construction
        retrieved_data = retriever.retrieve_with_graph_context(query=query, n_results=4)

        # 2. Build exact Sherpa prompt
        sherpa_messages = build_sherpa_prompt(query, retrieved_data)
        sherpa_tokens = count_message_tokens(sherpa_messages, enc)

        # 3. Extract unique files containing chunks and build baseline prompt
        chunk_files = extract_file_paths_for_chunks(retrieved_data, collection)
        baseline_messages = build_baseline_prompt(query, chunk_files, ROOT_DIR)
        baseline_tokens = count_message_tokens(baseline_messages, enc)

        reduction_pct = ((baseline_tokens - sherpa_tokens) / baseline_tokens * 100.0) if baseline_tokens > 0 else 0.0

        total_sherpa_tokens += sherpa_tokens
        total_baseline_tokens += baseline_tokens

        results.append({
            "query": query,
            "sherpa_tokens": sherpa_tokens,
            "baseline_tokens": baseline_tokens,
            "reduction_pct": f"{reduction_pct:.2f}%",
            "primary_nodes_count": len(retrieved_data.get("primary_nodes", [])),
            "downstream_nodes_count": len(retrieved_data.get("downstream_context", [])),
            "unique_files_count": len(chunk_files),
        })

        q_display = query if len(query) <= 45 else query[:42] + "..."
        print(f"{i:<3} | {q_display:<45} | {sherpa_tokens:<8} | {baseline_tokens:<9} | {reduction_pct:>8.2f}%")

    avg_sherpa = total_sherpa_tokens / len(queries)
    avg_baseline = total_baseline_tokens / len(queries)
    avg_reduction = ((avg_baseline - avg_sherpa) / avg_baseline * 100.0) if avg_baseline > 0 else 0.0

    print("-" * 85)
    print("\nBENCHMARK SUMMARY:")
    print(f"Total Queries Evaluated:       {len(queries)}")
    print(f"Average Tokens (Sherpa):       {avg_sherpa:.2f}")
    print(f"Average Tokens (Baseline):     {avg_baseline:.2f}")
    print(f"Overall Token Reduction:       {avg_reduction:.2f}%")

    # Write results to CSV
    csv_file = ROOT_DIR / "results.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "query",
            "sherpa_tokens",
            "baseline_tokens",
            "reduction_pct",
            "primary_nodes_count",
            "downstream_nodes_count",
            "unique_files_count",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nPer-query detailed results written to: {csv_file.name}")


if __name__ == "__main__":
    run_benchmark()
