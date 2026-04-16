import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
import json
from app.engine_ast.analyzer import build_unified_model
from app.engine_rag.chunker import SmartChunker
from app.engine_rag.retriever import GraphRetriever

print("Building unified model...")
analysis_result = build_unified_model("d:/CODE Sherpa/CODE_Sherpa/backend/app/engine_rag")
with open("test_analysis.json", "w") as f:
    json.dump(analysis_result, f, indent=2)

print("Extracting chunks...")
chunker = SmartChunker("test_analysis.json", "d:/CODE Sherpa/CODE_Sherpa/backend/app/engine_rag")
chunks = chunker.extract_chunks()

print(f"Extracted {len(chunks)} chunks.")

print("Validating retriever...")
# To not mess with user's db, we just instantiate a local persistent client
import chromadb
client = chromadb.PersistentClient(path="./chroma_test_data")
collection = client.get_or_create_collection("test_collection")

ids = [c["id"] for c in chunks]
docs = [c["text"] for c in chunks]
metas = [c["metadata"] for c in chunks]

# upsert
collection.upsert(ids=ids, documents=docs, metadatas=metas)

class MockDB:
    def __init__(self):
        self.collection = collection

retriever = GraphRetriever(MockDB())
result = retriever.retrieve_with_graph_context("what does the file vector_db.py do?", n_results=1)
print("PRIMARY NODES:")
for node in result["primary_nodes"]:
    print(node["node_id"])

# show prompt
prompt = retriever.format_llm_prompt(result, "what does the file vector_db.py do?")
print("PROMPT LENGTH:", len(prompt))
