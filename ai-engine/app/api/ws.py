from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, Query, HTTPException, status, Path
import logging
import json # For sending simple JSON responses like errors
from urllib.parse import parse_qs # Import to parse query parameters

# Using an async function directly instead of Depends for WebSocket context
from app.core.auth import validate_jwt_token
from app.llm.openai_client import stream_chat_completion

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
    """
    WebSocket endpoint that FOR THIS STEP:
    1. Authenticates user via JWT token passed as a query parameter ('token').
    2. Accepts the connection if authentication is successful.
    3. Logs received messages and the authenticated user ID.
    NO DATABASE INTERACTIONS IN THIS STEP.
    """
    try:
        # Extract token from websocket query_string
        query_string = websocket.scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        
        # Get token from query parameters
        token = query_params.get("token", [None])[0]
        logger.debug(f"WebSocket token present: {bool(token)}")
        
        if not token:
            logger.warning("WebSocket connection rejected: Missing token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Authenticate using the new validate_jwt_token function
        try:
            authed_user_id = validate_jwt_token(token)
        except HTTPException as auth_exc:
            logger.warning(f"WebSocket authentication failed: {auth_exc.detail}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Authentication successful - accept the connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for authed_user_id: {authed_user_id} to conversation_id: {conversation_id}")

        # For this step, we are not checking conversation ownership against the DB.
        # We are only verifying the token and getting the user_id.

        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from authed_user_id: {authed_user_id} for conversation_id: {conversation_id}: {data}")
            
            # Simple LLM call with the message - no history
            try:
                logger.info(f"Calling LLM with message: {data}")
                async for chunk in stream_chat_completion([
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": data}
                ]):
                    await websocket.send_text(chunk)
            except Exception as e:
                logger.error(f"Error in LLM call: {e}")
                await websocket.send_text("Error processing your request")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation_id: {conversation_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket for conversation_id: {conversation_id}: {e}", exc_info=True)
        # Ensure graceful closure if possible, though WebSocket might already be gone
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            except RuntimeError: 
                pass # Catch if sending close is not possible
    finally:
        logger.info(f"WebSocket for conversation_id: {conversation_id} - cleanup complete.")

# Need to import WebSocketState for the final finally block if it's not auto-imported with WebSocket
from starlette.websockets import WebSocketState 