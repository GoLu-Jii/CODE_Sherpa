import logging
import os
from typing import Any, Dict, List

from groq import Groq

from .prompts import SYSTEM_PROMPT, build_user_prompt

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

    context = format_graph_chunks(retrieved_chunk)
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
