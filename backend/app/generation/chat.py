# import os
# import requests
# from typing import List, Dict, Any
# from dotenv import load_dotenv
# from groq import Groq

# from .prompts import SYSTEM_PROMPT, build_user_prompt

# load_dotenv()
# groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from groq import Groq

from .prompts import SYSTEM_PROMPT, build_user_prompt

# --- BULLETPROOF .ENV LOADING ---
# 1. Get the directory of this current file (generation/chat.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Go up three levels to the CODE_SHERPA root folder
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../"))

# 3. Target the .env file explicitly
ENV_PATH = os.path.join(ROOT_DIR, ".env")

# 4. Load it!
load_dotenv(dotenv_path=ENV_PATH)

# Retrieve the key to verify it actually loaded
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(f"❌ CRITICAL: Groq API key not found! I looked exactly here: {ENV_PATH}")
else:
    print(f"✅ Groq Key Loaded Successfully: {api_key[:4]}...{api_key[-4:]}")

groq_client = Groq(api_key=api_key)

# 1. FIX: Format the specific arrays inside the Graph dictionary
def format_graph_chunks(retrieval_data: Dict[str, Any]) -> str:
    context_block = []
    
    # Format Primary Nodes
    for node in retrieval_data.get("primary_nodes", []):
        block = (
            f"PRIMARY NODE [{node.get('node_id')}]\n"
            f"Explicitly calls: {node.get('calls')}\n"
            f"Code:\n{node.get('code')}\n"
        )
        context_block.append(block)

    # Format Downstream Dependencies
    for dep in retrieval_data.get("downstream_context", []):
        block = (
            f"DEPENDENCY CONTEXT [{dep.get('node_id')}]\n"
            f"Code:\n{dep.get('code')}\n"
        )
        context_block.append(block)

    return "\n---\n".join(context_block)

# 2. FIX: Extract sources by checking both primary and downstream nodes
def extract_graph_sources(answer: str, retrieval_data: Dict[str, Any]) -> List[Dict]:
    sources = []
    
    # Combine all nodes we fed to the LLM
    all_nodes = retrieval_data.get("primary_nodes", []) + retrieval_data.get("downstream_context", [])
    
    for node in all_nodes:
        c_id = node.get("node_id")
        # If the LLM cited the node ID in its answer, add it to sources
        if c_id and f"[{c_id}]" in answer:
            sources.append({"node_id": c_id})

    return sources

def generate_answer(
        query: str,
        retrieved_chunk: Dict[str, Any],
) -> Dict:

    # 3. FIX: Check if the primary_nodes array is actually empty
    if not retrieved_chunk.get("primary_nodes"):
        return {
            "answer": "I could not find relevant code in the repository to answer this query.",
            "sources": [],
            "retrieved_chunks": retrieved_chunk,
        }

    # Pass the dictionary to our updated formatter
    context = format_graph_chunks(retrieved_chunk)
    user_prompt = build_user_prompt(query, context)

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1, 
            max_tokens=1024,
        )

    except Exception as e:
        raise RuntimeError(f"Groq request failed: {e}")

    answer_text = response.choices[0].message.content.strip()

    if not answer_text:
        return {
            "answer": "I don't know.",
            "sources": [],
            "retrieved_chunks": retrieved_chunk,
        }

    # Use the updated extraction function
    sources = extract_graph_sources(answer_text, retrieved_chunk)

    return {
        "answer": answer_text,
        "sources": sources,
        "retrieved_chunks": retrieved_chunk,
    }