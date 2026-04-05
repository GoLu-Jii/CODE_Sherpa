import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

# Import your core RAG engine tools
from backend.app.engine_rag.vector_db import ChromaCloudDB
from backend.app.engine_rag.retriever import GraphRetriever

# Import your Groq generation logic
from backend.app.generation.chat import generate_answer

# Set up logging for cloud deployment
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# --- INITIALIZE GLOBAL ENGINE ---
# We initialize the database connection outside the route.
# This prevents FastAPI from opening a new DB connection every time a user sends a message.
try:
    db = ChromaCloudDB(collection_name="codesherpa_real_repo")
    retriever = GraphRetriever(db)
    logger.info("✅ SherpaChat Router connected to Chroma Cloud successfully.")
except Exception as e:
    logger.error(f"❌ SherpaChat Router failed to connect to Chroma: {e}")

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
    try:
        logger.info(f"Incoming SherpaChat query: '{req.query}'")

        # retrieve from chroma 
        retrieved_data = retriever.retrieve_with_graph_context(query=req.query, n_results=1)

        formatted_history = [{"role": msg.role, "content": msg.content} for msg in req.history]

        # llm output
        ans = generate_answer(query=req.query, retrieved_chunk= retrieved_data, history=formatted_history)

        return{
            "status": "success",
            "data": ans
        }

        
    except Exception as e:
        logger.error(f"sherpachat execution failed..!")
        raise HTTPException(status_code=500, detail=f"chat generation failed: {str(e)}")
    