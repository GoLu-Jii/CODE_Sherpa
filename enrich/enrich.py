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
        # Add path to file_node for explanation helpers
        file_node.setdefault("path", file_path)
        
        file_node.setdefault(
            "explanation",
            _explain_file(file_node, use_llm)
        )

        # functions is a dict: {"func_name": {"calls": [...]}, ...}
        functions = file_node.get("functions", {})
        for func_name, func_node in functions.items():
            # Add name to func_node for explanation helpers
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
        return f"This file contains core logic defined in `{path}`."

    # functions is a dict: {"func_name": {"calls": [...]}, ...}
    functions = file_node.get("functions", {})
    function_names = list(functions.keys()) if isinstance(functions, dict) else []
    
    prompt = f"""
You are given verified static analysis data.

File path: {path}
Defined functions: {function_names}

Explain the purpose of this file using ONLY this information.
Do not infer runtime behavior.
Do not invent relationships.
Keep it concise.
"""

    return _safe_llm_call(prompt, fallback=f"This file defines logic in `{path}`.")


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
        if calls:
            return f"`{name}` coordinates calls to {', '.join(calls)}."
        return f"`{name}` performs a self-contained operation."

    prompt = f"""
You are given verified static analysis data.

Function name: {name}
Defined in file: {file_path}
Calls: {calls}

Explain the role of this function using ONLY this data.
Do not guess runtime behavior.
Do not invent relationships.
Keep it concise and factual.
"""

    fallback = (
        f"`{name}` coordinates calls to {', '.join(calls)}."
        if calls else
        f"`{name}` performs a self-contained operation."
    )

    return _safe_llm_call(prompt, fallback=fallback)


# -------------------------
# LLM interaction
# -------------------------

def _safe_llm_call(prompt: str, fallback: str) -> str:
    """
    Calls the LLM safely.
    If anything fails, returns fallback explanation.
    """

    try:
        return _call_llm(prompt)
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
                        "You explain existing code structure. "
                        "You are not allowed to infer behavior, "
                        "invent relationships, or guess intent."
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
