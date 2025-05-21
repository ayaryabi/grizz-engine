#!/usr/bin/env python3
"""
LLM Worker - Processes jobs from Redis queue and calls OpenAI

This worker:
1. Reads from the Redis queue using consumer groups
2. Processes chat completion requests
3. Streams results back to clients via Redis
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
from typing import Dict, Any, List, Optional

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import redis.asyncio as redis
from app.core.redis_client import get_redis_pool, close_redis_pool, LLM_JOBS_STREAM, RESULT_STREAM, LLM_JOBS_DEAD
from app.core.queue import move_to_dead_letter, publish_result_chunk
from app.llm.openai_client import AsyncOpenAI, stream_chat_completion
from app.services.memory_service import fetch_recent_messages
from app.agents.chat_agent import build_prompt
from app.db.database import get_async_db, async_session_maker
from app.core.config import get_settings
from app.db.models import Message
from sqlalchemy import insert, update
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("llm_worker")

# Worker settings
WORKER_ID = os.environ.get("WORKER_ID", f"worker-{uuid.uuid4()}")
CONSUMER_GROUP = "llm_workers"
MAX_RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds

# Global variables for graceful shutdown
shutdown_event = asyncio.Event()

async def process_chat_job(
    redis_conn: redis.Redis, 
    job_data: Dict[str, Any]
) -> bool:
    """
    Process a chat completion job
    
    Args:
        redis_conn: Redis connection
        job_data: Job data from Redis
        
    Returns:
        bool: True if successful, False otherwise
    """
    job_id = job_data.get("job_id", "unknown")
    user_id = job_data.get("user_id")
    conversation_id = job_data.get("conversation_id")
    message = job_data.get("message")
    
    # Extract metadata
    try:
        metadata_str = job_data.get("metadata", "{}")
        metadata = json.loads(metadata_str)
        client_id = metadata.get("client_id", "unknown-client")
    except json.JSONDecodeError:
        logger.error(f"Invalid metadata JSON for job {job_id}")
        metadata = {}
        client_id = "unknown-client"
    
    logger.info(f"Processing chat job {job_id} for conversation {conversation_id}")
    
    # Create database session
    db = async_session_maker()
    try:
        # 1. Fetch conversation context
        context = await fetch_recent_messages(conversation_id, db)
        
        # 2. Build the prompt for the LLM
        messages = build_prompt(context, message)
        
        # 3. Stream response from OpenAI and publish chunks as they arrive
        full_response = ""
        async for chunk in stream_chat_completion(messages):
            # Publish the chunk to Redis for immediate streaming to client
            await publish_result_chunk(
                redis_conn, 
                job_id, 
                chunk, 
                client_id, 
                is_final=False
            )
            full_response += chunk
        
        # 4. After all chunks are received, save the complete assistant message to the database
        #    Only save if full_response is not empty (OpenAI might return an empty stream on rare occasions or if content is just an error message from stream_chat_completion)
        if full_response: # stream_chat_completion yields error messages as strings too
            ai_message = Message(
                conversation_id=uuid.UUID(conversation_id),
                user_id=user_id,
                role="assistant",
                content=full_response,  # Use the accumulated full response
                message_metadata={"completed": True} # Mark as completed
            )
            db.add(ai_message)
            await db.commit()
            # await db.refresh(ai_message) # Not strictly needed if we don't use the ai_message object further
            logger.info(f"Saved full assistant message for job {job_id} to database.")
        else:
            logger.warning(f"Job {job_id} resulted in an empty full_response. Nothing saved to assistant message history.")

        # 5. Send final message to client to indicate end of streaming
        await publish_result_chunk(
            redis_conn, 
            job_id, 
            "\n\n[End of response]", 
            client_id, 
            is_final=True
        )
        
        logger.info(f"Successfully processed job {job_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
        # Notify the client that there was an error
        try:
            error_message = f"\n\n[Error: {str(e)}]"
            await publish_result_chunk(redis_conn, job_id, error_message, client_id, is_final=True)
        except Exception as notify_error:
            logger.error(f"Failed to notify client of error: {str(notify_error)}")
        return False
    finally:
        await db.close()

async def worker_loop():
    """Main worker loop that processes jobs from Redis"""
    redis_conn = await get_redis_pool()
    
    # Register with consumer group
    logger.info(f"Worker {WORKER_ID} started in consumer group {CONSUMER_GROUP}")
    
    while not shutdown_event.is_set():
        try:
            # Read new messages from the stream using consumer group
            streams = await redis_conn.xreadgroup(
                CONSUMER_GROUP,
                WORKER_ID,
                {LLM_JOBS_STREAM: ">"},  # > means "give me undelivered messages"
                count=1,
                block=5000  # 5 second timeout
            )
            
            if not streams:
                # No new messages, try again
                continue
                
            stream_name, messages = streams[0]
            
            if not messages:
                # No new messages, try again
                continue
                
            # Process each message
            message_id, data = messages[0]
            logger.info(f"Worker {WORKER_ID} received job: {message_id}")
            
            # Check for retry count
            retry_count = int(data.get("retry_count", "0"))
            
            # Process the job
            success = await process_chat_job(redis_conn, data)
            
            if success:
                # Acknowledge the message (mark as processed)
                await redis_conn.xack(LLM_JOBS_STREAM, CONSUMER_GROUP, message_id)
                await redis_conn.xdel(LLM_JOBS_STREAM, message_id)
                logger.info(f"Job {data.get('job_id', 'unknown')} completed and acknowledged")
            else:
                # Job failed
                if retry_count < MAX_RETRY_COUNT:
                    # Increment retry count and try again later
                    data["retry_count"] = str(retry_count + 1)
                    data["last_error_time"] = str(time.time())
                    
                    # Acknowledge current ID to remove from pending
                    await redis_conn.xack(LLM_JOBS_STREAM, CONSUMER_GROUP, message_id)
                    
                    # Add back to stream with updated retry info
                    await redis_conn.xadd(LLM_JOBS_STREAM, data)
                    
                    # Delete the original message
                    await redis_conn.xdel(LLM_JOBS_STREAM, message_id)
                    
                    logger.warning(f"Job {data.get('job_id')} failed, requeued for retry {retry_count + 1}/{MAX_RETRY_COUNT}")
                    
                    # Wait before processing more messages (to prevent rapid retries)
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    # Max retries exceeded, move to dead letter queue
                    await move_to_dead_letter(
                        redis_conn,
                        message_id,
                        data,
                        "Max retry count exceeded"
                    )
                    logger.error(f"Job {data.get('job_id')} failed after {MAX_RETRY_COUNT} retries, moved to dead letter queue")
            
        except asyncio.CancelledError:
            logger.info(f"Worker {WORKER_ID} cancelled")
            break
        except Exception as e:
            logger.error(f"Error in worker loop: {str(e)}", exc_info=True)
            # Sleep briefly to prevent error loops
            await asyncio.sleep(1)

async def handle_pending_jobs():
    """Check for and handle any pending jobs from previous runs"""
    redis_conn = await get_redis_pool()
    
    # Claim pending jobs from Redis
    pending = await redis_conn.xpending(LLM_JOBS_STREAM, CONSUMER_GROUP)
    
    if pending["pending"] > 0:
        logger.info(f"Found {pending['pending']} pending jobs from previous runs")
        
        # Get details on pending jobs
        pending_jobs = await redis_conn.xpending_range(
            LLM_JOBS_STREAM, 
            CONSUMER_GROUP,
            "-",  # minimum ID
            "+",  # maximum ID
            pending["pending"]
        )
        
        for job in pending_jobs:
            msg_id = job["message_id"]
            consumer = job["consumer"]
            idle_time = job.get("idle", 0)  # Use .get() with a default value of 0
            
            # If job has been idle for more than 30 seconds, claim it
            if idle_time > 30000:  # 30 seconds in milliseconds
                claimed = await redis_conn.xclaim(
                    LLM_JOBS_STREAM,
                    CONSUMER_GROUP,
                    WORKER_ID,
                    min_idle_time=30000,
                    message_ids=[msg_id]
                )
                
                if claimed:
                    logger.info(f"Claimed pending job {msg_id} from {consumer}")
                    
                    # Get the job data
                    job_data = claimed[0][1]
                    
                    # Process the job
                    retry_count = int(job_data.get("retry_count", "0"))
                    
                    if retry_count < MAX_RETRY_COUNT:
                        # Increment retry count and process
                        job_data["retry_count"] = str(retry_count + 1)
                        job_data["reclaimed"] = "true"
                        
                        # Process the job
                        success = await process_chat_job(redis_conn, job_data)
                        
                        if success:
                            # Acknowledge the message
                            await redis_conn.xack(LLM_JOBS_STREAM, CONSUMER_GROUP, msg_id)
                            await redis_conn.xdel(LLM_JOBS_STREAM, msg_id)
                            logger.info(f"Reclaimed job {job_data.get('job_id', 'unknown')} completed")
                        else:
                            # Failed to process
                            if retry_count + 1 < MAX_RETRY_COUNT:
                                # Still has retries left
                                logger.warning(f"Reclaimed job failed, will be retried")
                            else:
                                # Move to dead letter queue
                                await move_to_dead_letter(
                                    redis_conn,
                                    msg_id,
                                    job_data,
                                    "Max retry count exceeded after reclaiming"
                                )
                    else:
                        # Already at max retries, move to dead letter
                        await move_to_dead_letter(
                            redis_conn,
                            msg_id,
                            job_data,
                            "Max retry count exceeded"
                        )

def handle_signals():
    """Set up signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown")
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main worker function"""
    # Set up logging and signals
    handle_signals()
    
    try:
        # Initialize Redis
        await get_redis_pool()
        
        # Try to create the consumer group (if not exists)
        redis_conn = await get_redis_pool()
        try:
            await redis_conn.xgroup_create(
                LLM_JOBS_STREAM, 
                CONSUMER_GROUP, 
                mkstream=True, 
                id="0"
            )
            logger.info(f"Created consumer group '{CONSUMER_GROUP}'")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{CONSUMER_GROUP}' already exists")
            else:
                raise
        
        # Handle any pending jobs from previous runs
        await handle_pending_jobs()
        
        # Start worker loop
        await worker_loop()
        
    except Exception as e:
        logger.error(f"Fatal error in worker: {str(e)}", exc_info=True)
    finally:
        # Clean up resources
        await close_redis_pool()
        logger.info("Worker shutdown complete")

if __name__ == "__main__":
    asyncio.run(main()) 