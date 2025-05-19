#!/usr/bin/env python3
import asyncio
import websockets
import logging
import sys
import argparse
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("ws-test")

# Test WebSocket connection
async def test_websocket(url):
    logger.info(f"Connecting to WebSocket at {url}")
    try:
        async with websockets.connect(url) as websocket:
            logger.info("Connection established successfully!")
            
            # Send a simple message
            message = "Hello from test client"
            logger.info(f"Sending message: {message}")
            await websocket.send(message)
            
            # Wait for a response with a timeout
            logger.info("Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                logger.info(f"Received response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for response")
                
            # Keep connection open for a few seconds
            logger.info("Keeping connection open for 5 seconds...")
            await asyncio.sleep(5)
            
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"WebSocket connection closed with code {e.code}: {e.reason}")
    except Exception as e:
        logger.error(f"Error: {e}")

# Main function
async def main():
    parser = argparse.ArgumentParser(description='Test WebSocket connection')
    parser.add_argument('--conv', required=True, help='Conversation ID')
    parser.add_argument('--token', required=True, help='JWT token')
    parser.add_argument('--host', default='ai-engine-lingering-feather-7082.fly.dev', help='WebSocket host')
    
    args = parser.parse_args()
    
    # URL encode the token to handle special characters
    token_encoded = urllib.parse.quote(args.token)
    
    # Build WebSocket URL
    url = f"wss://{args.host}/ws/chat/{args.conv}?token={token_encoded}"
    
    await test_websocket(url)

if __name__ == "__main__":
    asyncio.run(main()) 