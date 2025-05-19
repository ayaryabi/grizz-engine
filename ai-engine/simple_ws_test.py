#!/usr/bin/env python3
# Simple WebSocket test server - run with: uvicorn simple_ws_test:app --host 0.0.0.0 --port 8000

from fastapi import FastAPI, WebSocket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Simple WebSocket Test Server"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.websocket("/ws/simple-test")
async def websocket_test(websocket: WebSocket):
    logger.info("WebSocket connection attempt")
    
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message: {data}")
            
            # Simply echo back the message
            await websocket.send_text(f"Echo: {data}")
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 