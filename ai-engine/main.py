from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.ws import router as ws_router
# from app.api.db_test import router as db_test_router # Removed import
from app.api.conversation import router as conversation_router
from app.core.config import get_settings
from app.db.database import engine
from app.db import models
import uvicorn

# Create database tables
models.Base.metadata.create_all(bind=engine)

settings = get_settings()

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
# app.include_router(db_test_router, prefix="/test", tags=["test"]) # Removed usage
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
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Grizz Chat API is running"}
