from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.llm.openai_client import stream_chat_completion
import json

router = APIRouter()

@router.websocket("/ws/echo")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Build OpenAI messages format
            messages = [
                {"role": "user", "content": data}
            ]
            # Stream LLM response
            async for chunk in stream_chat_completion(messages):
                await websocket.send_text(chunk)
    except WebSocketDisconnect:
        pass 