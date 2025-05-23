from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, Query, HTTPException, status, Path
import logging
import json # For sending simple JSON responses like errors
import uuid
import asyncio
import json
import time
from urllib.parse import parse_qs # Import to parse query parameters
from app.core.auth import validate_jwt_token
from app.db.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from starlette.websockets import WebSocketState
from app.db.models import Message
from app.services.queue_service import queue_chat_message, listen_for_job_results

logger = logging.getLogger(__name__)
router = APIRouter()

# Default endpoint no longer needed since we're getting real conversation IDs
# @router.websocket("/ws/chat")
# async def websocket_default_chat_endpoint(websocket: WebSocket):
#     """Simplified WebSocket endpoint that uses 'test' as the default conversation ID."""
#     await websocket_chat_endpoint(websocket, "test")

@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    conversation_id: str = Path(..., description="Conversation ID"),
):
    async for db in get_async_db():
        try:
            # Log connection attempt details
            logger.info(f"WebSocket connection attempt - Headers: {websocket.headers}")
            logger.info(f"WebSocket connection attempt - Client: {websocket.client}")
            
            # More detailed query string logging
            query_string = websocket.scope.get("query_string", b"").decode()
            logger.info(f"WebSocket connection attempt - Query string raw: {query_string}")
            
            # Extract token from websocket query_string
            query_params = parse_qs(query_string)
            logger.info(f"WebSocket connection attempt - Parsed query params: {query_params}")
            
            token = query_params.get("token", [None])[0]
            logger.info(f"WebSocket token present: {bool(token)}")
            
            if not token:
                logger.warning("WebSocket connection rejected: Missing token")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            try:
                authed_user_id = validate_jwt_token(token)
                logger.info(f"Token validation successful for user: {authed_user_id}")
            except HTTPException as auth_exc:
                logger.error(f"WebSocket authentication failed: {auth_exc.detail}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            
            # Create a unique client ID for this websocket connection
            client_id = f"client:{uuid.uuid4()}"
            
            # Background task for listening to results
            listen_task = None
            
            # Track last activity time for idle timeout detection
            last_activity_time = time.time()
            
            # Background task to monitor idle connections
            idle_monitor_task = None
            
            logger.info("Attempting to accept WebSocket connection...")
            await websocket.accept()
            logger.info(f"WebSocket connection accepted for authed_user_id: {authed_user_id} to conversation_id: {conversation_id}")
            
            # Start idle connection monitor
            async def monitor_idle_connection():
                while True:
                    try:
                        # Check if connection is idle for more than 5 minutes (300s)
                        idle_seconds = time.time() - last_activity_time
                        if idle_seconds > 300:
                            logger.info(f"Closing idle WebSocket connection after {idle_seconds:.1f}s of inactivity for user {authed_user_id}")
                            # Use code 1000 (normal closure) so browsers don't treat it as an error
                            await websocket.close(code=1000)
                            break
                        await asyncio.sleep(60)  # Check every minute
                    except asyncio.CancelledError:
                        logger.debug("Idle monitor task cancelled")
                        break
                    except Exception as e:
                        logger.error(f"Error in idle connection monitor: {str(e)}")
                        await asyncio.sleep(60)  # Sleep and retry
            
            # Start the monitor task
            idle_monitor_task = asyncio.create_task(monitor_idle_connection())
            
            try:
                while True:
                    logger.debug("Waiting for message...")
                    message_data = await websocket.receive_text()
                    
                    # Update last activity time when message is received
                    last_activity_time = time.time()
                    
                    # Parse JSON if present, otherwise treat as plain text
                    try:
                        parsed_data = json.loads(message_data)
                        user_message = parsed_data.get('text', '')
                        file_urls = parsed_data.get('file_urls', [])
                    except (json.JSONDecodeError, TypeError):
                        user_message = message_data
                        file_urls = []
                    
                    logger.info(f"Received message from user {authed_user_id}: {user_message[:100]}...")  # Log first 100 chars
                    if file_urls:
                        logger.info(f"With {len(file_urls)} file(s): {[url.split('/')[-1] for url in file_urls]}")  # Log filenames
                    
                    # 1. Save user message to DB
                    try:
                        # Save file_urls in metadata if present
                        message_metadata = {"file_urls": file_urls} if file_urls else {}
                        
                        user_msg = Message(
                            conversation_id=uuid.UUID(conversation_id),
                            user_id=authed_user_id,
                            role="user",
                            content=user_message,
                            message_metadata=message_metadata
                        )
                        db.add(user_msg)
                        await db.commit()
                        await db.refresh(user_msg)
                        logger.info(f"Saved user message for conversation: {conversation_id}")
                    except Exception as db_error:
                        logger.error(f"Error saving user message: {str(db_error)}", exc_info=True)
                        await websocket.send_text("\n\n[Error: Could not save your message. Please try again.]")
                        continue
                    
                    # 2. Queue the chat message for processing
                    try:
                        # Add file_urls to metadata if present
                        metadata = {"file_urls": file_urls} if file_urls else None
                        
                        job_id = await queue_chat_message(
                            user_id=authed_user_id,
                            conversation_id=conversation_id,
                            message=user_message,
                            client_id=client_id,
                            metadata=metadata
                        )
                        
                        logger.info(f"Queued job {job_id} for conversation {conversation_id}")
                        
                        # Start the result listener task for this specific job
                        if listen_task and not listen_task.done():
                            listen_task.cancel()
                            try:
                                await listen_task
                            except asyncio.CancelledError:
                                pass
                        
                        listen_task = asyncio.create_task(
                            listen_for_job_results(
                                client_id=client_id,
                                result_callback=websocket.send_text,
                                job_id=job_id,
                                timeout_seconds=120  # 2 minute timeout
                            )
                        )
                        
                    except ValueError as e:
                        # System overloaded or other queue error
                        await websocket.send_text(
                            json.dumps({
                                "type": "error",
                                "message": str(e)
                            })
                        )
                    except Exception as e:
                        logger.error(f"Error queueing message: {str(e)}", exc_info=True)
                        await websocket.send_text("\n\n[Error: Could not process your message. Please try again.]")
                
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected for conversation_id: {conversation_id}")
            finally:
                # Clean up background tasks
                if listen_task and not listen_task.done():
                    listen_task.cancel()
                    try:
                        await listen_task
                    except asyncio.CancelledError:
                        pass
                
                if idle_monitor_task and not idle_monitor_task.done():
                    idle_monitor_task.cancel()
                    try:
                        await idle_monitor_task
                    except asyncio.CancelledError:
                        pass
        except Exception as e:
            logger.error(f"Error in WebSocket for conversation_id: {conversation_id}: {str(e)}", exc_info=True)
            if websocket.client_state != WebSocketState.DISCONNECTED:
                try:
                    await websocket.close(code=1001)  # Going away
                except RuntimeError as re: 
                    logger.error(f"Error closing websocket: {str(re)}")
                    pass
        finally:
            logger.info(f"WebSocket for conversation_id: {conversation_id} - cleanup complete.") 