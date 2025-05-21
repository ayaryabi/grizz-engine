import json
import uuid
import time
import asyncio
from typing import Dict, Any, Optional, List
import logging
import redis.asyncio as redis
from app.core.redis_client import (
    get_redis_pool, 
    LLM_JOBS_STREAM, 
    RESULT_STREAM, 
    LLM_JOBS_DEAD,
    safe_redis_operation
)

logger = logging.getLogger(__name__)

# Backpressure thresholds
MAX_PENDING_JOBS = 5000
RATE_LIMIT_THRESHOLD = 3000

async def get_pending_job_count() -> int:
    """Get count of pending jobs in the queue"""
    redis_conn = await get_redis_pool()
    try:
        info = await safe_redis_operation(redis_conn.xinfo_stream, LLM_JOBS_STREAM)
        return info["length"]
    except redis.ResponseError:
        # Stream doesn't exist yet
        return 0
    except Exception as e:
        logger.error(f"Error getting pending job count: {str(e)}")
        return 0  # Return 0 on error to avoid false backpressure alerts

async def check_backpressure() -> int:
    """
    Check if system is under backpressure
    
    Returns:
        int: Current pending job count
        
    Raises:
        ValueError: If system is overloaded
    """
    count = await get_pending_job_count()
    if count > MAX_PENDING_JOBS:
        logger.error(f"BACKPRESSURE: System critically overloaded with {count} pending jobs. Rejecting request.")
        raise ValueError(f"System overloaded with {count} pending jobs")
    elif count > RATE_LIMIT_THRESHOLD:
        logger.warning(f"BACKPRESSURE: Approaching overload with {count} pending jobs. Applying 1s delay.")
        await asyncio.sleep(1.0)  # Slow down
    return count

async def enqueue_chat_job(
    redis_conn: redis.Redis,
    user_id: str, 
    conversation_id: str, 
    message: str, 
    metadata: Optional[Dict] = None
) -> str:
    """
    Add a chat message job to the LLM jobs queue.
    
    Args:
        redis_conn: Redis connection from pool
        user_id: User ID for the message
        conversation_id: Conversation ID
        message: User's message content
        metadata: Additional metadata (e.g., client_id)
        
    Returns:
        str: The job ID
    """
    job_id = str(uuid.uuid4())
    
    # Use a single hierarchical dict structure
    job_data = {
        "job_id": job_id,
        "type": "chat_completion",
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message": message,
        # Store metadata as a JSON string
        "metadata": json.dumps(metadata or {}),
        "timestamp": time.time(),
        "status": "pending"
    }
    
    # Add to Redis Stream with error handling
    try:
        msg_id = await safe_redis_operation(redis_conn.xadd, LLM_JOBS_STREAM, job_data, id="*")
        logger.info(f"Enqueued chat job {job_id} (msg_id: {msg_id}) for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Failed to enqueue job {job_id}: {str(e)}")
        raise ValueError(f"Failed to enqueue message: {str(e)}") from e
    
    # Trim is now handled by the periodic maintenance task in redis_client.py
    # This avoids unnecessary Redis operations on every job
    
    return job_id

async def publish_result_chunk(
    redis_conn: redis.Redis,
    job_id: str, 
    chunk: str, 
    client_id: str, 
    is_final: bool = False
) -> None:
    """
    Publish a chunk of the LLM response to the result stream.
    
    Args:
        redis_conn: Redis connection from pool
        job_id: ID of the job this result belongs to
        chunk: Text chunk from LLM
        client_id: WebSocket client ID to filter results
        is_final: Whether this is the final chunk
    """
    result_data = {
        "job_id": job_id,
        "client_id": client_id,  # Include client_id for security filtering
        "chunk": chunk,
        "is_final": "true" if is_final else "false",  # Simple string, no need for json.dumps
        "timestamp": time.time()
    }
    
    try:
        await safe_redis_operation(redis_conn.xadd, RESULT_STREAM, result_data, id="*")
        
        # Only trim on final chunk to reduce Redis operations
        if is_final:
            await safe_redis_operation(
                redis_conn.xtrim, 
                RESULT_STREAM, 
                maxlen=50000, 
                approximate=True
            )
        
        logger.debug(f"Published result chunk for job {job_id}, final: {is_final}")
    except Exception as e:
        logger.error(f"Failed to publish chunk for job {job_id}: {str(e)}")
        # Don't raise here - we want the worker to continue even if publishing fails

async def move_to_dead_letter(
    redis_conn: redis.Redis,
    message_id: str, 
    job_data: Dict, 
    error: str
) -> None:
    """
    Move a failed job to the dead letter queue
    
    Args:
        redis_conn: Redis connection from pool
        message_id: Redis message ID
        job_data: Original job data
        error: Error message
    """
    # Add error info
    job_data["error"] = error
    job_data["failed_at"] = time.time()
    
    try:
        # Add to dead letter queue
        await safe_redis_operation(redis_conn.xadd, LLM_JOBS_DEAD, job_data, id="*")
        
        # Remove from main queue
        await safe_redis_operation(redis_conn.xack, LLM_JOBS_STREAM, "llm_workers", message_id)
        await safe_redis_operation(redis_conn.xdel, LLM_JOBS_STREAM, message_id)
        
        logger.warning(f"Moved job {job_data.get('job_id')} to dead letter queue: {error}")
    except Exception as e:
        logger.error(f"Failed to move job to dead letter queue: {str(e)}")
        # Try to acknowledge the message to prevent reprocessing, even if move failed
        try:
            await redis_conn.xack(LLM_JOBS_STREAM, "llm_workers", message_id)
        except Exception:
            pass 