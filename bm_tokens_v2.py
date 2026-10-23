#!/usr/bin/env python3
"""
bm_tokens_v2.py
---------------
Token benchmark for CODE Sherpa.

For each query in queries.txt:
  - Run the real retrieval pipeline (same GraphRetriever + Chroma store as production).
  - Build the exact prompt Sherpa sends to the LLM (system + context + question).
  - Build a baseline prompt using the FULL file contents of every file that
    contains at least one retrieved chunk.
  - Count tokens with tiktoken (cl100k_base).

Reports:
  - Per-query rows: query type, Sherpa tokens, Baseline tokens, reduction %, chunk IDs.
  - Overall average and % reduction.
  - Per query-type averages (function-level, who-calls, module-level).
  - Sherpa wins vs. losses (queries where Sherpa sends fewer tokens than baseline).
  - Identical-prompt detection: flags queries that produced the exact same
    Sherpa prompt and shows which chunks were retrieved + why.

Output:
  - Console (raw terminal output).
  - bm_tokens_v2.csv  (per-query details).

Rules:
  - Does NOT modify any file in backend/ or .env.
  - Does NOT print or log API keys.
  - Uses the same Chroma store as production (CHROMA_LOCAL=true, chroma_data/).
"""

import csv
import os
import re
import sys
from collections import defaultdict
from hashlib import md5
from pathlib import Path
from typing import Any, Dict, List, Set

import dotenv
import tiktoken
import chromadb

# UTF-8 output on Windows
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
from app.generation.chat import generate_mermaid_graph, format_graph_chunks
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt


def classify_query(query: str) -> str:
    q = query.lower().strip()
    if q.startswith("who calls"):
        return "who-calls"
    if re.match(r"how does module", q):
        return "module-level"
    return "function-level"


def get_encoder():
    return tiktoken.get_encoding("cl100k_base")


def count_message_tokens(messages: List[Dict[str, str]], enc) -> int:
    n = 0
    for msg in messages:
        n += 4
        for val in msg.values():
            n += len(enc.encode(str(val)))
    n += 2
    return n


def build_sherpa_prompt(query: str, retrieved_data: Dict[str, Any]) -> List[Dict[str, str]]:
    if not retrieved_data.get("primary_nodes"):
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "I could not find relevant code in the repository to answer this query."},
        ]
    mermaid = generate_mermaid_graph(retrieved_data)
    chunks = format_graph_chunks(retrieved_data)
    context = (
        f"Graph Structure (Mermaid):\n```mermaid\n{mermaid}\n```\n\nCode Chunks:\n{chunks}"
        if mermaid else chunks
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(query, context)},
    ]


def extract_file_paths(retrieved_data: Dict[str, Any], collection) -> Set[str]:
    all_nodes = retrieved_data.get("primary_nodes", []) + retrieved_data.get("downstream_context", [])
    paths: Set[str] = set()
    for node in all_nodes:
        nid = node.get("node_id")
        code = node.get("code", "")
        m = re.search(r"^File:\s*([^\r\n]+)", code, re.MULTILINE)
        if m:
            paths.add(m.group(1).strip())
            continue
        if nid and collection is not None:
            try:
                res = collection.get(ids=[nid], include=["metadatas"])
                fp = (res.get("metadatas") or [{}])[0].get("file_path")
                if fp:
                    paths.add(fp)
            except Exception:
                pass
    return paths


def build_baseline_prompt(query: str, file_paths: Set[str], repo_root: Path) -> List[Dict[str, str]]:
    if not file_paths:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "I could not find relevant code in the repository to answer this query."},
        ]
    blocks = []
    for rel in sorted(file_paths):
        full = repo_root / rel
        if not full.exists():
            alt = repo_root / "backend" / rel
            if alt.exists():
                full = alt
        if full.exists() and full.is_file():
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                content = f"# Error reading {rel}: {e}"
        else:
            content = f"# File not found on disk: {rel}"
        blocks.append(f"FILE: {rel}\n```python\n{content}\n```")
    context = "\n\n---\n\n".join(blocks)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(query, context)},
    ]


def run():
    queries_file = ROOT_DIR / "queries.txt"
    if not queries_file.exists():
        print(f"ERROR: {queries_file} not found.", file=sys.stderr)
        sys.exit(1)

    queries = [l.strip() for l in queries_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Loaded {len(queries)} queries from {queries_file.name}")

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "chroma_data")
    chroma_path = ROOT_DIR / persist_dir
    print(f"Chroma store : {chroma_path}  (CHROMA_LOCAL={os.getenv('CHROMA_LOCAL')})")
    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection("codesherpa_real_repo")
    print(f"Collection   : codesherpa_real_repo  ({collection.count()} chunks)\n")

    retriever = GraphRetriever(type("DB", (), {"collection": collection})())
    enc = get_encoder()

    rows = []
    sherpa_wins = 0
    sherpa_loses = 0
    prompt_hash_to_queries: Dict[str, List[int]] = defaultdict(list)
    type_sherpa: Dict[str, List[int]] = defaultdict(list)
    type_baseline: Dict[str, List[int]] = defaultdict(list)

    hdr = f"{'#':>3}  {'Type':^13}  {'Query':<45}  {'Sherpa':>7}  {'Baseline':>8}  {'Reduc%':>7}  {'Chunks p/d':>11}"
    print(hdr)
    print("-" * len(hdr))

    for i, query in enumerate(queries, 1):
        qtype = classify_query(query)
        retrieved = retriever.retrieve_with_graph_context(query=query, n_results=4)
        sherpa_msgs = build_sherpa_prompt(query, retrieved)
        sherpa_tok = count_message_tokens(sherpa_msgs, enc)
        file_paths = extract_file_paths(retrieved, collection)
        baseline_msgs = build_baseline_prompt(query, file_paths, ROOT_DIR)
        baseline_tok = count_message_tokens(baseline_msgs, enc)
        pct = (baseline_tok - sherpa_tok) / baseline_tok * 100.0 if baseline_tok > 0 else 0.0

        user_content = sherpa_msgs[-1]["content"] if sherpa_msgs else ""
        h = md5(user_content.encode("utf-8")).hexdigest()
        prompt_hash_to_queries[h].append(i)

        primary_ids = [n.get("node_id", "?") for n in retrieved.get("primary_nodes", [])]
        downstream_ids = [n.get("node_id", "?") for n in retrieved.get("downstream_context", [])]

        rows.append({
            "idx": i,
            "query_type": qtype,
            "query": query,
            "sherpa_tokens": sherpa_tok,
            "baseline_tokens": baseline_tok,
            "reduction_pct": round(pct, 2),
            "primary_nodes": len(primary_ids),
            "downstream_nodes": len(downstream_ids),
            "unique_files": len(file_paths),
            "primary_chunk_ids": "; ".join(primary_ids),
            "downstream_chunk_ids": "; ".join(downstream_ids),
            "prompt_hash": h,
        })

        if sherpa_tok < baseline_tok:
            sherpa_wins += 1
        else:
            sherpa_loses += 1

        type_sherpa[qtype].append(sherpa_tok)
        type_baseline[qtype].append(baseline_tok)

        q_disp = query if len(query) <= 45 else query[:42] + "..."
        chunk_info = f"{len(primary_ids)}p/{len(downstream_ids)}d"
        print(f"{i:>3}  {qtype:^13}  {q_disp:<45}  {sherpa_tok:>7,}  {baseline_tok:>8,}  {pct:>6.2f}%  {chunk_info:>11}")

    print("-" * len(hdr))
    n = len(queries)
    avg_s = sum(r["sherpa_tokens"] for r in rows) / n
    avg_b = sum(r["baseline_tokens"] for r in rows) / n
    avg_pct = (avg_b - avg_s) / avg_b * 100.0 if avg_b > 0 else 0.0

    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print(f"{'='*60}")
    print(f"  Queries evaluated        : {n}")
    print(f"  Avg Sherpa tokens        : {avg_s:,.1f}")
    print(f"  Avg Baseline tokens      : {avg_b:,.1f}")
    print(f"  Overall token reduction  : {avg_pct:.2f}%")
    print(f"  Sherpa uses fewer tokens : {sherpa_wins} / {n}  (wins)")
    print(f"  Sherpa uses MORE tokens  : {sherpa_loses} / {n}  (losses)")

    print(f"\n{'='*60}")
    print("BY QUERY TYPE")
    print(f"{'='*60}")
    print(f"  {'Type':<15}  {'N':>4}  {'Avg Sherpa':>10}  {'Avg Baseline':>12}  {'Avg Reduc%':>10}")
    for qtype in ["function-level", "who-calls", "module-level"]:
        ss = type_sherpa.get(qtype, [])
        bs = type_baseline.get(qtype, [])
        if not ss:
            continue
        ts = sum(ss) / len(ss)
        tb = sum(bs) / len(bs)
        tp = (tb - ts) / tb * 100.0 if tb > 0 else 0.0
        print(f"  {qtype:<15}  {len(ss):>4}  {ts:>10,.1f}  {tb:>12,.1f}  {tp:>9.2f}%")

    duplicates = {h: idxs for h, idxs in prompt_hash_to_queries.items() if len(idxs) > 1}
    print(f"\n{'='*60}")
    print("IDENTICAL PROMPT DETECTION")
    print(f"{'='*60}")
    if not duplicates:
        print("  No queries produced identical Sherpa prompts.")
    else:
        print(f"  {len(duplicates)} group(s) of queries share an identical Sherpa prompt:\n")
        for h, idxs in duplicates.items():
            print(f"  Hash {h[:12]}...  -- queries #{', #'.join(str(x) for x in idxs)}:")
            for idx in idxs:
                r = rows[idx - 1]
                print(f"    Q{idx}: \"{r['query']}\"")
                print(f"         primary chunks   : {r['primary_chunk_ids'] or '(none)'}")
                print(f"         downstream chunks: {r['downstream_chunk_ids'] or '(none)'}")
            print()
        print("  WHY identical? The retriever resolves chunks by deterministic ID/name")
        print("  lookup (exact qualified_name or function_name match), not semantic")
        print("  search. If two queries name the same symbol or file, they resolve")
        print("  to the same chunk set and therefore produce the same prompt content.")

    csv_out = ROOT_DIR / "bm_tokens_v2.csv"
    fieldnames = [
        "idx", "query_type", "query",
        "sherpa_tokens", "baseline_tokens", "reduction_pct",
        "primary_nodes", "downstream_nodes", "unique_files",
        "primary_chunk_ids", "downstream_chunk_ids", "prompt_hash",
    ]
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nDetailed results written to: {csv_out.name}")


if __name__ == "__main__":
    run()
