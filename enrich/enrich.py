"""
Semantic enrichment layer.

Purpose:
- Add natural-language explanations to static analysis output.
- NEVER change structure, ordering, or relationships.
- LLM is non-authoritative: AST-derived data remains the source of truth.
"""

import json
import os
import requests
from copy import deepcopy
from typing import Dict, Any

# -------------------------
# LLM configuration
# -------------------------

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"
TEMPERATURE = 0.2
TIMEOUT_SECONDS = 20


# -------------------------
# Public API
# -------------------------

def enrich_analysis(analysis: Dict[str, Any], use_llm: bool = True) -> Dict[str, Any]:
    """
    Enrich the analysis dict with explanations.

    Rules:
    - MUST NOT add/remove nodes
    - MUST NOT reorder lists
    - MAY only append explanation-related fields
    """

    enriched = deepcopy(analysis)
    files = enriched.get("files", {})

    for file_path, file_node in files.items():
        # Attach path for explanation helpers
        file_node.setdefault("path", file_path)

        file_node.setdefault(
            "explanation",
            _explain_file(file_node, use_llm)
        )

        functions = file_node.get("functions", {})
        for func_name, func_node in functions.items():
            func_node.setdefault("name", func_name)

            func_node.setdefault(
                "explanation",
                _explain_function(func_node, file_node, use_llm)
            )

    return enriched


def enrich_file(input_path: str, output_path: str, use_llm: bool = True) -> None:
    """
    File-based entrypoint used by CLI.
    """

    with open(input_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    enriched = enrich_analysis(analysis, use_llm=use_llm)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)


# -------------------------
# Explanation helpers
# -------------------------

def _explain_file(file_node: Dict[str, Any], use_llm: bool) -> str:
    """
    Generate a file-level explanation.
    """

    path = file_node.get("path", "this file")

    if not use_llm:
        return (
            "The role of this file cannot be determined from static structure alone."
        )

    functions = file_node.get("functions", {})
    function_names = list(functions.keys()) if isinstance(functions, dict) else []

    prompt = f"""
You are given verified static analysis data.

File path: {path}
Defined functions: {function_names}

Explain the role of this file in a codebase.

Rules:
- You may use common programming conventions and file naming patterns.
- Do NOT invent runtime behavior or hidden relationships.
- If the role cannot be determined with confidence, state uncertainty explicitly.
- Prefer explaining relevance over listing contents.
- Avoid tautologies such as "defines logic".

Keep it concise (1–2 sentences).
"""

    fallback = (
        "The role of this file cannot be determined from static structure alone."
    )

    return _safe_llm_call(prompt, fallback=fallback)


def _explain_function(
    fn_node: Dict[str, Any],
    file_node: Dict[str, Any],
    use_llm: bool
) -> str:
    """
    Generate a function-level explanation.
    """

    name = fn_node.get("name", "this function")
    calls = fn_node.get("calls", [])
    file_path = file_node.get("path", "unknown file")

    if not use_llm:
        return (
            f"`{name}` performs an internal operation, "
            "but its exact responsibility cannot be determined from static structure alone."
        )

    prompt = f"""
You are given verified static analysis data.

Function name: {name}
Defined in file: {file_path}
Calls: {calls}

Explain what this function appears to be responsible for.

Rules:
- You may interpret function names and standard library calls.
- Do NOT invent runtime behavior or external interactions.
- If responsibility cannot be inferred, state uncertainty explicitly.
- Do NOT describe the function by listing its calls.
- Focus on developer-relevant understanding.

Keep it concise (1 sentence).
"""

    fallback = (
        f"`{name}` performs an internal operation, "
        "but its exact responsibility cannot be determined from static structure alone."
    )

    return _safe_llm_call(prompt, fallback=fallback)


# -------------------------
# Explanation quality gate
# -------------------------

def _is_bad_explanation(text: str) -> bool:
    """
    Detect low-signal or tautological explanations.
    """

    banned_phrases = [
        "defines logic",
        "coordinates calls",
        "handles various",
        "responsible for various",
    ]

    lower = text.lower()
    return any(phrase in lower for phrase in banned_phrases)


# -------------------------
# LLM interaction
# -------------------------

def _safe_llm_call(prompt: str, fallback: str) -> str:
    """
    Calls the LLM safely.
    If anything fails or output violates quality rules,
    returns the fallback explanation.
    """

    try:
        result = _call_llm(prompt)
        if _is_bad_explanation(result):
            return fallback
        return result
    except Exception:
        return fallback


def _call_llm(prompt: str) -> str:
    """
    Low-level LLM call.
    This is the ONLY place that talks to the model.
    """

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")

    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You explain code structure for developer understanding. "
                        "You may rely on common programming conventions, "
                        "standard library semantics, and identifier names. "
                        "You MUST NOT invent relationships or runtime behavior. "
                        "If intent or purpose cannot be proven from static structure, "
                        "you MUST state uncertainty explicitly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": TEMPERATURE,
        },
        timeout=TIMEOUT_SECONDS,
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()
