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

# Import the generation function from your new generation directory
from generation.chat import generate_answer

# Mute chromadb's internal logs to keep your terminal clean
logging.getLogger("chromadb").setLevel(logging.WARNING)

def run_full_pipeline_test():
    print("\n" + "="*60)
    print("🧠 TESTING FULL GRAPH-RAG PIPELINE (WITH GROQ LLM)")
    print("="*60 + "\n")

    # 1. Initialize DB (Skipping re-ingestion since it is already in the cloud)
    print("⚙️  Connecting to Chroma Cloud Database...")
    db = ChromaCloudDB(collection_name="codesherpa_real_repo")
    
    # UNCOMMENT the below 3 lines ONLY if you change the sample_repo code and need to re-upload
    # chunker = SmartChunker(analysis_file_path=ANALYSIS_PATH, repo_base_path=REPO_PATH)
    # chunks = chunker.extract_chunks()
    # db.ingest_chunks(chunks)

    # 2. Retrieve Data
    retriever = GraphRetriever(db)
    
    # Test both exact symbol lookup and conceptual query
    test_queries = [
        "what does src.requests.api.get do",  # Exact qualified symbol lookup
        "what does get_connection do",  # Partial symbol lookup
        "how are HTTP connections managed?"  # Conceptual query
    ]
    
    for user_query in test_queries:
        print(f"\n🎯 Querying Chroma: '{user_query}'")
        retrieval_data = retriever.retrieve_with_graph_context(query=user_query, n_results=1)

        print(f"   -> Found {len(retrieval_data.get('primary_nodes', []))} primary nodes.")
        print(f"   -> Found {len(retrieval_data.get('downstream_context', []))} downstream dependencies.")
        
        if retrieval_data.get('primary_nodes'):
            print(f"   -> Primary node: {retrieval_data['primary_nodes'][0]['node_id']}")

    # Use the exact symbol query for the full pipeline test
    user_query = "what does the function _basic_auth_str do?"
    retrieval_data = retriever.retrieve_with_graph_context(query=user_query, n_results=1)

    # 3. Generate Answer via LLM
    print("\n🤖 Sending structured graph context to Groq (Llama-3)...")
    print(f"\n🎯 Querying Chroma for final symbol query: '{user_query}'")
    print(f"   -> Found {len(retrieval_data.get('primary_nodes', []))} primary nodes.")
    print(f"   -> Found {len(retrieval_data.get('downstream_context', []))} downstream dependencies.")
    if retrieval_data.get('primary_nodes'):
        print(f"   -> Primary node: {retrieval_data['primary_nodes'][0]['node_id']}")

    try:
        llm_result = generate_answer(query=user_query, retrieved_chunk=retrieval_data)
        
        print("\n" + "-"*50)
        print("📝 FINAL CODE SHERPA ANSWER:")
        print("-" *50)
        print(llm_result["answer"])
        
        print("\n" + "-"*50)
        print("🔗 ACCURATE CITED SOURCES (AST Nodes):")
        print("-" *50)
        if not llm_result.get("sources"):
            print("No explicit sources cited.")
        else:
            for source in llm_result["sources"]:
                print(f" - [{source['node_id']}]")
            
    except Exception as e:
        print(f"\n❌ LLM Generation Failed: {e}")

    print("\n" + "="*60)
    print("✅ FULL PIPELINE TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_full_pipeline_test()