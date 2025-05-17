from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, Query, HTTPException
from app.llm.openai_client import stream_chat_completion
from app.db.database import get_db
from app.db.models import User, Conversation, Message
from sqlalchemy.orm import Session
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

@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    conversation_id: str,
    user_id: str = Query(..., description="User ID"),
):
    """
    WebSocket endpoint that:
    1. Accepts connection with conversation_id and user_id
    2. Saves user messages to database
    3. Streams AI responses and saves them to database
    """
    await websocket.accept()
    
    # Get DB session - we'll create a new session for each message
    # to avoid keeping the session open for the entire WebSocket connection
    
    try:
        # Initial validation
        db = next(get_db())
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.send_text(json.dumps({
                "error": "User not found"
            }))
            await websocket.close()
            return
        
        # Verify conversation exists and belongs to user
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if not conversation:
            await websocket.send_text(json.dumps({
                "error": "Conversation not found or access denied"
            }))
            await websocket.close()
            return
        
        # Get previous messages from this conversation (for context)
        # In a real implementation, we might limit this or handle pagination
        previous_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        # Convert to OpenAI message format
        openai_messages = []
        for msg in previous_messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        db.close()  # Close initial validation session
        
        # Main message loop
        while True:
            # Wait for a message from the client
            data = await websocket.receive_text()
            
            try:
                # Parse message data
                message_data = json.loads(data)
                message_text = message_data.get("message", "")
                
                # Create a new DB session for this message
                db = next(get_db())
                
                # Save user message to database
                user_message = Message(
                    conversation_id=conversation_id,
                    role="user",
                    content=message_text
                )
                db.add(user_message)
                db.commit()
                
                # Add to context for OpenAI
                openai_messages.append({
                    "role": "user",
                    "content": message_text
                })
                
                # Create AI message in database (we'll update content as it streams)
                ai_message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=""  # Will be updated as content streams
                )
                db.add(ai_message)
                db.commit()
                db.refresh(ai_message)
                
                # Stream completion from OpenAI
                full_response = ""
                async for chunk in stream_chat_completion(openai_messages):
                    full_response += chunk
                    await websocket.send_text(chunk)
                
                # Update the AI message with the complete response
                ai_message.content = full_response
                db.commit()
                
                # Add to context for next messages
                openai_messages.append({
                    "role": "assistant",
                    "content": full_response
                })
                
                # Close this message's DB session
                db.close()
                
            except json.JSONDecodeError:
                await websocket.send_text("Error: Invalid JSON message format")
            except Exception as e:
                await websocket.send_text(f"Error: {str(e)}")
                if 'db' in locals() and db is not None:
                    db.close()
                
    except WebSocketDisconnect:
        # Clean up on disconnect
        if 'db' in locals() and db is not None:
            db.close() 