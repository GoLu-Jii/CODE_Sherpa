import tempfile
import subprocess
import os
import json

from backend.app.engine_rag.chunker import SmartChunker
from backend.app.engine_rag.vector_db import ChromaCloudDB

from backend.app.engine_ast.analyzer import build_unified_model
from backend.app.engine_ast.flowchart.flow_builder import build_simple_file_graph
from backend.app.engine_ast.flowchart.exporter import export_mermaid


# temporary clone the github repo 

def ingest_github_repo(repo_url: str) -> dict:
    """Clones, analyzes, ingests to Chroma, and returns the Mermaid string for React."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📥 Cloning the repo into temporary directory: {temp_dir}")
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        
        # 1. Run AST analysis
        print("🔍 Running AST analysis...")
        analysis_result = build_unified_model(temp_dir)
        
        # 2. Temporarily save analysis.json for the Chunker
        analysis_file = os.path.join(temp_dir, "analysis.json")
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=2)
            
        # 3. Chunk and upload to Chroma Cloud
        print("⚙️ Chunking and uploading to Chroma Cloud...")
        chunker = SmartChunker(analysis_file, temp_dir)
        chunks = chunker.extract_chunks()
        
        db = ChromaCloudDB(collection_name="codesherpa_real_repo")
        db.ingest_chunks(chunks)
        
        # 4. Generate the Flowchart inside the Temp Directory
        print("🗺️ Generating flowchart.md...")
        graph = build_simple_file_graph(analysis_result)
        
        flowchart_file = os.path.join(temp_dir, "flowchart.md")
        export_mermaid(graph, flowchart_file) # Your existing function writes to the temp file
        
        # 5. Read the Mermaid text OUT of the file before the temp folder deletes itself
        with open(flowchart_file, "r", encoding="utf-8") as f:
            mermaid_string = f.read()
            
        print("🧹 Ingestion completed. Wiping temporary files from server.")
            
    # 6. Send Mermaid text + raw AST data to the frontend
    return {
        "status": "success",
        "message": "Repository fully mapped and ingested.",
        "mermaid_chart": mermaid_string,
        "raw_ast": {
            "entry_point": analysis_result.get("entry_point"),
            "files": analysis_result.get("files", {}),
            "graph": graph  # nodes + edges already computed for Mermaid
        }
    }


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class IngestRequest(BaseModel):
    repo_url: str

@router.post("/github-repo")
async def ingest_github_repo_endpoint(request: IngestRequest):
    try:
        result = ingest_github_repo(request.repo_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest repository: {str(e)}")