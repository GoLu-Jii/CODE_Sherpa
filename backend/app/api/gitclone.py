import tempfile
import subprocess
import os
import json
import uuid
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.engine_rag.chunker import SmartChunker
from app.engine_rag.vector_db import ChromaCloudDB
from app.engine_ast.analyzer import build_unified_model
from app.engine_ast.flowchart.flow_builder import build_simple_file_graph
from app.engine_ast.flowchart.exporter import export_mermaid


# In-memory job store
jobs: Dict[str, Any] = {}


def ingest_github_repo(job_id: str, repo_url: str):
    try:
        jobs[job_id] = {"status": "cloning", "message": "Cloning repository..."}

        with tempfile.TemporaryDirectory() as temp_dir:

            result = subprocess.run(
                ["git", "clone", "--depth=1", repo_url, temp_dir],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                jobs[job_id] = {
                    "status": "failed",
                    "message": f"Git clone failed: {result.stderr.strip()}"
                }
                return

            jobs[job_id] = {"status": "analyzing", "message": "Running AST analysis..."}
            analysis_result = build_unified_model(temp_dir)

            # Attach file source text so frontend can render code tabs and function bodies.
            for file_path, file_meta in analysis_result.get("files", {}).items():
                source_path = os.path.join(temp_dir, file_path)
                try:
                    with open(source_path, "r", encoding="utf-8") as source_file:
                        file_meta["source"] = source_file.read()
                except FileNotFoundError:
                    file_meta["source"] = ""

            analysis_file = os.path.join(temp_dir, "analysis.json")
            with open(analysis_file, "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, indent=2)

            jobs[job_id] = {"status": "ingesting", "message": "Uploading to vector database..."}
            chunker = SmartChunker(analysis_file, temp_dir)
            chunks = chunker.extract_chunks()

            db = ChromaCloudDB(collection_name="codesherpa_real_repo")
            db.ingest_chunks(chunks)

            jobs[job_id] = {"status": "charting", "message": "Generating architecture graph..."}
            graph = build_simple_file_graph(analysis_result)

            flowchart_file = os.path.join(temp_dir, "flowchart.md")
            export_mermaid(graph, flowchart_file)

            with open(flowchart_file, "r", encoding="utf-8") as f:
                mermaid_string = f.read()

        jobs[job_id] = {
            "status": "complete",
            "message": "Repository fully mapped and ingested.",
            "mermaid_chart": mermaid_string,
            "raw_ast": {
                "entry_point": analysis_result.get("entry_point"),
                "files": analysis_result.get("files", {}),
                "graph": graph
            }
        }

    except Exception as e:
        jobs[job_id] = {
            "status": "failed",
            "message": str(e)
        }


router = APIRouter()


class IngestRequest(BaseModel):
    repo_url: str


@router.post("/github-repo")
async def ingest_github_repo_endpoint(request: IngestRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "message": "Job queued."}
    background_tasks.add_task(ingest_github_repo, job_id, request.repo_url)
    return {"status": "queued", "job_id": job_id}


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.post("/reset")
async def reset_session_endpoint():
    try:
        db = ChromaCloudDB(collection_name="codesherpa_real_repo")
        db.clear_collection()

        db_ast = ChromaCloudDB(collection_name="codesherpa_ast")
        db_ast.clear_collection()

        return {"status": "success", "message": "Chroma DB collections cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear collections: {str(e)}")