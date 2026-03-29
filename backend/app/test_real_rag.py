import os
import json
import logging
from dotenv import load_dotenv

# Resolve absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../"))

ENV_PATH = os.path.join(ROOT_DIR, ".env")
ANALYSIS_PATH = os.path.join(ROOT_DIR, "demo/analysis.json")
REPO_PATH = os.path.join(ROOT_DIR, "sample_repo")

load_dotenv(dotenv_path=ENV_PATH)

from engine_rag.chunker import SmartChunker
from engine_rag.vector_db import ChromaCloudDB
from engine_rag.retriever import GraphRetriever

# Mute chromadb's internal logs to keep your terminal clean
logging.getLogger("chromadb").setLevel(logging.WARNING)

def run_retrieval_test():
    print("\n" + "="*60)
    print("🔍 TESTING GRAPH-RAG RETRIEVAL (NO LLM)")
    print("="*60 + "\n")

    # 1. Chunk and Ingest (Skip if you already ingested successfully before)
    print("⚙️  Chunking and Ingesting Data...")
    chunker = SmartChunker(analysis_file_path=ANALYSIS_PATH, repo_base_path=REPO_PATH)
    chunks = chunker.extract_chunks()
    
    db = ChromaCloudDB(collection_name="codesherpa_real_repo")
    db.ingest_chunks(chunks)

    # 2. Retrieve
    retriever = GraphRetriever(db)
    user_query = "What happens when I call api.get() and what functions does it depend on?"
    
    print(f"\n🎯 Querying: '{user_query}'")
    retrieval_data = retriever.retrieve_with_graph_context(query=user_query, n_results=1)

    # 3. Print the raw data to verify the engine works
    print("\n" + "-"*30)
    print("📍 1. PRIMARY NODES FOUND (Semantic Search)")
    print("-"*30)
    for node in retrieval_data["primary_nodes"]:
        print(f"Node ID:  {node['node_id']}")
        print(f"Calls:    {node['calls']}")
        print(f"Code Snippet (First 3 lines):\n{chr(10).join(node['code'].split(chr(10))[:3])}...")

    print("\n" + "-"*30)
    print("🔗 2. DOWNSTREAM CONTEXT FETCHED (Graph Traversal)")
    print("-"*30)
    if not retrieval_data["downstream_context"]:
        print("No downstream dependencies found.")
    else:
        for dep in retrieval_data["downstream_context"]:
            print(f"Node ID:  {dep['node_id']}")
            print(f"Code Snippet (First 3 lines):\n{chr(10).join(dep['code'].split(chr(10))[:3])}...\n")

    print("\n" + "="*60)
    print("✅ ENGINE TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_retrieval_test()