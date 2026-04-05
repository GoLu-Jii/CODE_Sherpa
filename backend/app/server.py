from fastapi import FastAPI
from dotenv import load_dotenv

# Load your environment variables for Groq and Chroma
load_dotenv()

# Import your separated routers
from backend.app.api.sherpachat import router as chat_router
from backend.app.api.gitclone import router as clone_router

app = FastAPI(title="CODE Sherpa API", version="1.0")

# Plug the routes into the web server
app.include_router(chat_router, prefix="/api/v1/sherpachat", tags=["Conversational AI"])
app.include_router(clone_router, prefix="/api/v1/ingest", tags=["Repository Processing"])

@app.get("/")
async def health_check():
    return {"status": "online", "message": "CODE Sherpa Web Server is running!"}