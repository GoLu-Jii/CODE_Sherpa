from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load your environment variables for Groq and Chroma
load_dotenv()

# Import your separated routers
from app.api.sherpachat import router as chat_router
from app.api.gitclone import router as clone_router
from app.engine_rag.vector_db import ChromaCloudDB
from app.engine_rag.retriever import GraphRetriever

retriever: GraphRetriever = None

logger = logging.getLogger(__name__)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup logic
#     yield
#     # Shutdown logic: wipe out the temporary vector data
#     logger.info("Server is shutting down. Clearing ChromaDB collections...")
#     try:
#         db = ChromaCloudDB(collection_name="codesherpa_real_repo")
#         db.clear_collection()
#     except Exception as e:
#         logger.error(f"Error while cleaning collection 'codesherpa_real_repo': {e}")
        
#     try:
#         db_ast = ChromaCloudDB(collection_name="codesherpa_ast")
#         db_ast.clear_collection()
#     except Exception as e:
#         logger.error(f"Error while cleaning collection 'codesherpa_ast': {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever
    try:
        db = ChromaCloudDB(collection_name="codesherpa_real_repo")
        
        # Clear any stale data from previous session (crash recovery)
        db.clear_collection()
        logger.info("Cleared stale collection on startup.")
        
        retriever = GraphRetriever(db)
        logger.info("Connected to Chroma Cloud successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize on startup: {e}")
        retriever = None

    yield

    # Clean shutdown
    logger.info("Server shutting down. Clearing collections...")
    try:
        db = ChromaCloudDB(collection_name="codesherpa_real_repo")
        db.clear_collection()
    except Exception as e:
        logger.error(f"Error clearing collection on shutdown: {e}")

app = FastAPI(title="CODE Sherpa API", version="1.0", lifespan=lifespan)

# -------------------------------------------------------------------
# CORS — Allow the Vite frontend (and any origin in dev) to talk to us
# -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://code-sherpa.vercel.app",
        "https://code-sherpa-gauravj121232-5882s-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plug the routes into the web server
app.include_router(chat_router, prefix="/api/v1/sherpachat", tags=["Conversational AI"])
app.include_router(clone_router, prefix="/api/v1/ingest", tags=["Repository Processing"])

@app.get("/")
async def health_check():
    return {"status": "online", "message": "CODE Sherpa Web Server is running!"}