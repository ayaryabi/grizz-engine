from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, Query, HTTPException, status, Path
import logging
import json # For sending simple JSON responses like errors
from urllib.parse import parse_qs # Import to parse query parameters
from app.core.auth import validate_jwt_token
from app.services.chat_service import handle_chat_message
from app.db.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketState

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

            logger.info("Attempting to accept WebSocket connection...")
            await websocket.accept()
            logger.info(f"WebSocket connection accepted for authed_user_id: {authed_user_id} to conversation_id: {conversation_id}")

            while True:
                logger.debug("Waiting for message...")
                data = await websocket.receive_text()
                logger.info(f"Received message from user {authed_user_id}: {data[:100]}...")  # Log first 100 chars
                
                await handle_chat_message(
                    user_id=authed_user_id,
                    conversation_id=conversation_id,
                    user_message=data,
                    db=db,
                    stream_callback=websocket.send_text
                )
        except WebSocketDisconnect:
            logger.warning(f"WebSocket disconnected for conversation_id: {conversation_id}")
            break
        except Exception as e:
            logger.error(f"Error in WebSocket for conversation_id: {conversation_id}: {str(e)}", exc_info=True)
            if websocket.client_state != WebSocketState.DISCONNECTED:
                try:
                    await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                except RuntimeError as re: 
                    logger.error(f"Error closing websocket: {str(re)}")
                    pass
            break
        finally:
            logger.info(f"WebSocket for conversation_id: {conversation_id} - cleanup complete.") 