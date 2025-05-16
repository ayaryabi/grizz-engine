from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Grizz Chat API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
