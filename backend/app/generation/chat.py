import logging
import os
from typing import Any, Dict, List

from groq import Groq

from .prompts import SYSTEM_PROMPT, build_user_prompt
from app.engine_ast.flowchart.flow_builder import node_id

logger = logging.getLogger(__name__)
groq_client = None


def get_groq_client() -> Groq:
    global groq_client
    if groq_client is not None:
        return groq_client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    groq_client = Groq(api_key=api_key)
    logger.info("Groq client initialized.")
    return groq_client


def format_graph_chunks(retrieval_data: Dict[str, Any]) -> str:
    context_block = []

    for node in retrieval_data.get("primary_nodes", []):
        block = (
            f"PRIMARY NODE [{node.get('node_id')}]\n"
            f"Explicitly calls: {node.get('calls')}\n"
            f"Code:\n{node.get('code')}\n"
        )
        context_block.append(block)

    for dep in retrieval_data.get("downstream_context", []):
        block = (
            f"DEPENDENCY CONTEXT [{dep.get('node_id')}]\n"
            f"Code:\n{dep.get('code')}\n"
        )
        context_block.append(block)

    return "\n---\n".join(context_block)


def get_node_group(nid: str) -> str:
    if nid.startswith("src.") or nid.startswith("src/"):
        return "source"
    if nid.startswith("tests.") or nid.startswith("tests/"):
        return "tests"
    if nid.startswith("docs.") or nid.startswith("docs/"):
        return "docs"
    return "project"


def generate_mermaid_graph(retrieval_data: Dict[str, Any]) -> str:
    primary_nodes = retrieval_data.get("primary_nodes", [])
    downstream_context = retrieval_data.get("downstream_context", [])
    
    if not primary_nodes and not downstream_context:
        return ""
        
    lines = ["graph TD"]
    
    groups = {
        "source": "Source",
        "project": "Project",
        "tests": "Tests",
        "docs": "Docs",
        "unknown": "Unknown"
    }
    
    nodes_by_group = {k: [] for k in groups.keys()}
    seen_nodes = set()
    all_retrieved = []
    
    # Collect all unique node IDs
    for node in primary_nodes:
        nid = node.get("node_id")
        if nid and nid not in seen_nodes:
            seen_nodes.add(nid)
            all_retrieved.append((nid, True))
            
    for dep in downstream_context:
        nid = dep.get("node_id")
        if nid and nid not in seen_nodes:
            seen_nodes.add(nid)
            all_retrieved.append((nid, False))

    for nid, is_primary in all_retrieved:
        safe_id = node_id(nid)
        group = get_node_group(nid)
        label = f"{nid} (Primary)" if is_primary else nid
        nodes_by_group.setdefault(group, []).append((safe_id, label))
        
    # Build subgraphs matching exporter.py style
    for group_key, group_title in groups.items():
        nodes = nodes_by_group.get(group_key, [])
        if not nodes:
            continue
        lines.append(f"subgraph {group_title}")
        for safe_id, label in sorted(nodes, key=lambda x: x[1]):
            lines.append(f'  {safe_id}["{label}"]')
        lines.append("end")
        
    # Build edges between retrieved nodes
    retrieved_safe_ids = {node_id(nid) for nid, _ in all_retrieved}
    
    for node in primary_nodes:
        src = node.get("node_id")
        calls = node.get("calls", [])
        if not src or not calls:
            continue
        safe_src = node_id(src)
        for dst in calls:
            safe_dst = node_id(dst)
            if safe_dst in retrieved_safe_ids:
                lines.append(f"  {safe_src} --> {safe_dst}")
                
    return "\n".join(lines)



def extract_graph_sources(answer: str, retrieval_data: Dict[str, Any]) -> List[Dict[str, str]]:
    sources = []
    all_nodes = retrieval_data.get("primary_nodes", []) + retrieval_data.get("downstream_context", [])

    for node in all_nodes:
        node_id = node.get("node_id")
        if node_id and f"[{node_id}]" in answer:
            sources.append({"node_id": node_id})

    return sources


def generate_answer(
    query: str,
    retrieved_chunk: Dict[str, Any],
    history: List[Dict[str, str]] = None,
) -> Dict[str, Any]:
    if history is None:
        history = []

    if not retrieved_chunk.get("primary_nodes"):
        return {
            "answer": "I could not find relevant code in the repository to answer this query.",
            "sources": [],
            "retrieved_chunks": retrieved_chunk,
        }

    mermaid_graph = generate_mermaid_graph(retrieved_chunk)
    chunks_context = format_graph_chunks(retrieved_chunk)
    
    if mermaid_graph:
        context = f"Graph Structure (Mermaid):\n```mermaid\n{mermaid_graph}\n```\n\nCode Chunks:\n{chunks_context}"
    else:
        context = chunks_context

    user_prompt = build_user_prompt(query, context)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )
    except Exception as exc:
        raise RuntimeError(f"Groq request failed: {exc}") from exc

    answer_text = response.choices[0].message.content.strip()

    if not answer_text:
        return {
            "answer": "I don't know.",
            "sources": [],
            "retrieved_chunks": retrieved_chunk,
        }

    sources = extract_graph_sources(answer_text, retrieved_chunk)

    return {
        "answer": answer_text,
        "sources": sources,
        "retrieved_chunks": retrieved_chunk,
    }
