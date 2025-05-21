from app.core.redis_client import get_redis_pool, RESULT_STREAM, safe_redis_operation
from app.core.queue import enqueue_chat_job, check_backpressure, publish_result_chunk
import asyncio
import logging
import json
import uuid
import time
from typing import Callable, Any, Optional, Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)

async def queue_chat_message(
    user_id: str,
    conversation_id: str,
    message: str,
    client_id: str,
    metadata: Optional[Dict] = None
) -> str:
    """
    Queue a chat message for processing by a worker
    
    Args:
        user_id: User ID
        conversation_id: Conversation ID
        message: User message to process
        client_id: Client ID for the WebSocket connection
        metadata: Additional metadata
        
    Returns:
        str: Job ID
    """
    # Check for system overload
    try:
        await check_backpressure()
    except ValueError as e:
        logger.error(f"System overloaded, rejecting message: {str(e)}")
        raise
    
    # Get Redis connection
    redis_conn = await get_redis_pool()
    
    # Combine metadata
    full_metadata = metadata or {}
    full_metadata["client_id"] = client_id
    
    # Queue the job
    job_id = await enqueue_chat_job(
        redis_conn,
        user_id,
        conversation_id,
        message,
        full_metadata
    )
    
    logger.info(f"Queued chat message as job {job_id} for user {user_id}, conversation {conversation_id}")
    return job_id

async def listen_for_job_results(
    client_id: str,
    result_callback: Callable[[str], Any],
    job_id: Optional[str] = None,
    timeout_seconds: int = 120
) -> None:
    """
    Listen for results from a specific job or all jobs for this client
    
    Args:
        client_id: Client ID to filter results
        result_callback: Callback to send results (usually websocket.send_text)
        job_id: Optional specific job ID to listen for
        timeout_seconds: How long to listen before giving up
    """
    redis_conn = await get_redis_pool()
    
    # Keep track of the last ID we've seen
    last_id = "$"  # Special ID meaning "all new messages"
    
    # Track if we found any results
    received_results = False
    received_final = False
    
    # Start time for timeout calculation
    start_time = asyncio.get_event_loop().time()
    
    # Stream key to listen to
    stream_key = f"results:{client_id}"
    
    logger.info(f"Started listening for results for client: {client_id}" + 
                (f", job: {job_id}" if job_id else ""))
    
    try:
        while True:
            # Check for timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(f"Timeout waiting for results for client {client_id}")
                if not received_results:
                    # No results received at all, send a timeout message
                    try:
                        await result_callback("\n\n[Error: Request timed out. The system may be overloaded.]")
                    except Exception as e:
                        logger.error(f"Error sending timeout message: {str(e)}")
                break
            
            # Calculate remaining time for this timeout period
            remaining_time = max(1000, int((timeout_seconds - elapsed) * 1000))
            
            # Use a long blocking read (up to 15 seconds) to drastically reduce polling frequency
            # This is the key optimization to reduce Redis operations
            try:
                streams = await safe_redis_operation(
                    redis_conn.xread,
                    streams={RESULT_STREAM: last_id},
                    count=20,  # Process more messages at once
                    block=15000  # Block for up to 15 seconds
                )
            except ValueError as e:
                # Handle errors from safe_redis_operation
                logger.error(f"Redis error during blocking read: {str(e)}")
                try:
                    await result_callback("\n\n[Error: Server busy. Please try again later.]")
                except Exception as callback_err:
                    logger.error(f"Error sending error message: {str(callback_err)}")
                break
            except Exception as e:
                logger.error(f"Unexpected error during Redis read: {str(e)}")
                await asyncio.sleep(0.5)  # Brief pause on errors
                continue
            
            if not streams:  # No new messages after blocking period
                continue
                
            stream_name, messages = streams[0]
            
            for message_id, data in messages:
                # Update the last ID we've seen
                last_id = message_id
                
                result_job_id = data.get('job_id')
                result_client_id = data.get('client_id')
                chunk = data.get('chunk', '')
                is_final = data.get('is_final') == 'true'
                
                # Security check: only process results intended for this client
                if result_client_id != client_id:
                    continue
                
                # If specific job_id was provided, filter for that job
                if job_id and result_job_id != job_id:
                    continue
                
                # Update tracking variables
                received_results = True
                if is_final:
                    received_final = True
                
                # Send the chunk to the client
                try:
                    await result_callback(chunk)
                    logger.debug(f"Client {client_id}, Job {result_job_id}: Sent chunk via WebSocket. Final: {is_final}")
                except Exception as e:
                    logger.error(f"Error sending to callback for client {client_id}, job {result_job_id}: {str(e)}")
                    return # Exit if callback fails
                
                # If this is the final message and we were waiting for a specific job,
                # we can exit
                if is_final and job_id:
                    logger.info(f"Received final chunk for job {job_id}, listener exiting")
                    return
            
            # Also exit if we've processed the final message for any job
            if received_final:
                break
    
    except asyncio.CancelledError:
        # Task was cancelled, exit gracefully
        logger.debug(f"Result listener for {client_id} cancelled")
        raise
    except Exception as e:
        logger.error(f"Error in result listener: {str(e)}", exc_info=True)