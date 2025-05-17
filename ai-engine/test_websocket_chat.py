import asyncio
import websockets
import json
import sys
from test_conversation import test_create_user_if_needed, test_get_today_conversation

async def test_websocket_chat(user_id, conversation_id, messages=None):
    """Test the WebSocket chat endpoint with a conversation ID"""
    if messages is None:
        messages = ["Hello, how are you?", "Tell me about yourself"]
    
    uri = f"ws://localhost:8001/ws/chat/{conversation_id}?user_id={user_id}"
    
    try:
        async with websockets.connect(uri) as ws:
            print(f"Connected to WebSocket: {uri}")
            
            for i, message in enumerate(messages):
                print(f"\nSending message {i+1}: {message}")
                
                # Send message
                await ws.send(json.dumps({
                    "message": message
                }))
                
                # Receive streamed response
                print("AI response: ", end="", flush=True)
                full_response = ""
                
                while True:
                    try:
                        # Set a timeout to handle end of streaming
                        response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        print(response, end="", flush=True)
                        full_response += response
                    except asyncio.TimeoutError:
                        # Timeout means streaming has ended
                        break
                    except websockets.exceptions.ConnectionClosed:
                        print("\nConnection closed")
                        break
                
                print(f"\nFull response received, length: {len(full_response)}")
    
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    # Create a test user if needed
    user_id = test_create_user_if_needed()
    
    # Get today's conversation
    timezone = "America/Los_Angeles"
    if len(sys.argv) > 1:
        timezone = sys.argv[1]
    
    print(f"Testing with timezone: {timezone}")
    conversation_id = test_get_today_conversation(user_id, timezone)
    
    if conversation_id:
        # Test messages
        messages = [
            "Hello, can you help me with something?",
            "Tell me about the benefits of using FastAPI for backend development"
        ]
        
        # Test the WebSocket chat
        await test_websocket_chat(user_id, conversation_id, messages)
    else:
        print("Failed to get conversation ID, can't test WebSocket")

if __name__ == "__main__":
    asyncio.run(main()) 