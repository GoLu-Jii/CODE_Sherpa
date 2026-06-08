import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

# Import your core RAG engine tools
from app.engine_rag.vector_db import ChromaCloudDB
from app.engine_rag.retriever import GraphRetriever

# Import your Groq generation logic
from app.generation.chat import generate_answer

import app.server as state

# Set up logging for cloud deployment
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


# --- PYDANTIC SCHEMAS ---
class Message(BaseModel):
    role: str = Field(..., description="Must be 'user' or 'assistant'")
    content: str = Field(..., description="The text of the message")

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's newest question about the codebase")
    history: Optional[List[Message]] = Field(default=[], description="Previous conversation context for memory")

# api endpoint 

@router.post("/chat")
async def chat_with_engine(req: ChatRequest):
    if state.retriever is None:
        raise HTTPException(status_code=503, detail="Database not ready. Please ingest a repository first.")
    try:
        logger.info(f"Incoming SherpaChat query: '{req.query}'")

        retrieved_data = state.retriever.retrieve_with_graph_context(query=req.query, n_results=4)

        formatted_history = [{"role": msg.role, "content": msg.content} for msg in req.history]

        ans = generate_answer(query=req.query, retrieved_chunk=retrieved_data, history=formatted_history)

        return {
            "status": "success",
            "data": ans
        }

    except Exception as e:
        logger.error(f"sherpachat execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"chat generation failed: {str(e)}")
    