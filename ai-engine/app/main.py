from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.ws import router as ws_router
from app.api.conversation import router as conversation_router
from app.core.config import get_settings
from app.db.database import engine
from app.db import models
import uvicorn
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

settings = get_settings()

# Create FastAPI app with proper concurrency settings
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js frontend URL (development)
        "https://grizz.so",       # Production frontend
        "*",                      # Allow all origins temporarily for debugging
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(conversation_router, prefix="/api", tags=["conversations"])

class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat(message: ChatMessage):
    # For now, just echo back the message
    # Later we'll integrate with actual AI processing
    return {
        "response": f"Echo: {message.message}",
        "status": "success"
    }

@app.get("/health")
async def health_check():
    # This is an ultra-lightweight health check that will always respond quickly
    # It doesn't wait for database or any other resources
    return {"status": "healthy"}

@app.get("/")
async def root():
    # This is the endpoint used by Fly.io for health checks
    # Keep it super lightweight to ensure it never blocks
    return {"message": "Grizz Chat API is running"}

# This is only used when running the script directly (not through the Dockerfile)
if __name__ == "__main__":
    # Determine port and host from environment variables or use defaults
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Log startup information
    logger.info(f"Starting server on {host}:{port}")
    
    # Run with proper host binding
    uvicorn.run("app.main:app", host=host, port=port, reload=False) 