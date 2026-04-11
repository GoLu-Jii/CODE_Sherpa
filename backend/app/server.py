from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load your environment variables for Groq and Chroma
load_dotenv()

# Import your separated routers
from backend.app.api.sherpachat import router as chat_router
from backend.app.api.gitclone import router as clone_router

app = FastAPI(title="CODE Sherpa API", version="1.0")

# -------------------------------------------------------------------
# CORS — Allow the Vite frontend (and any origin in dev) to talk to us
# -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",   # in case of CRA / other setups
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