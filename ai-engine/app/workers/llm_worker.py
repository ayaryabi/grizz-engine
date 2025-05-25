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
import sentry_sdk
from app.core.sentry_context import set_user_context, set_redis_context, detect_race_condition_issues
from app.core.redis_client import (
    get_redis_pool, 
    close_redis_pool, 
    LLM_JOBS_STREAM, 
    safe_redis_operation
)
from app.core.queue import move_to_dead_letter, publish_result_chunk
# Agent SDK imports for streaming
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent

from app.services.memory_service import fetch_recent_messages
from app.agents.chat_agent import chat_agent
from app.db.database import async_session_maker
from app.db.models import Message
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
        file_urls = metadata.get("file_urls", [])
    except json.JSONDecodeError:
        logger.error(f"Invalid metadata JSON for job {job_id}")
        metadata = {}
        client_id = "unknown-client"
        file_urls = []
    
    logger.info(f"Processing chat job {job_id} for conversation {conversation_id}")
    
    # Set Sentry context for this job
    set_user_context(user_id=user_id, conversation_id=conversation_id)
    set_redis_context(stream_key=client_id, operation="process_job")
    
    # Create database session
    db = async_session_maker()
    full_response = ""
    loop = asyncio.get_event_loop()
    
    try:
        processing_start_time = loop.time()
        # 1. Fetch conversation context
        db_fetch_start_time = loop.time()
        context = await fetch_recent_messages(conversation_id, db)
        db_fetch_duration = loop.time() - db_fetch_start_time
        logger.info(f"Job {job_id}: Fetched context in {db_fetch_duration:.4f}s")
        
        # 2. Prepare input with context for Agent SDK
        agent_processing_start_time = loop.time()
        if file_urls:
            logger.info(f"Job {job_id}: Processing {len(file_urls)} file(s)")
        
        # Format conversation context for Agent SDK
        # Agent SDK will handle this better than manual prompt building
        conversation_input = chat_agent._format_conversation_for_agent_streaming(context, message, file_urls)
        
        agent_processing_duration = loop.time() - agent_processing_start_time
        logger.info(f"Job {job_id}: Prepared Agent SDK input in {agent_processing_duration:.4f}s")
        
        # 3. Stream response via Agent SDK using run_streamed
        openai_call_start_time = loop.time()
        
        # Proper Agent SDK streaming approach
        from agents import Runner
        from openai.types.responses import ResponseTextDeltaEvent
        
        # Use run_streamed for proper streaming
        # conversation_input is now either a List[dict] for multimodal or str for text-only
        if file_urls and len(file_urls) > 0:
            logger.info(f"Job {job_id}: Sending multimodal input with {len(file_urls)} image(s) to Agent SDK")
        
        streamed_result = Runner.run_streamed(chat_agent.agent, conversation_input)
        
        async def agent_chunks_iterator():
            """Convert Agent SDK streaming events to text chunks"""
            async for event in streamed_result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    yield event.data.delta
        
        chunks_iterator = agent_chunks_iterator()
        
        previous_chunk = None
        has_sent_chunks = False
        first_chunk_received = False

        async for current_chunk_content in chunks_iterator:
            if not first_chunk_received:
                first_chunk_time = loop.time() - openai_call_start_time
                logger.info(f"Job {job_id}: Time to first chunk from OpenAI: {first_chunk_time:.4f}s")
                first_chunk_received = True
            
            # Logic to send previous_chunk if it exists
            if previous_chunk is not None: 
                publish_start_time = loop.time()
                await publish_result_chunk(
                    redis_conn, 
                    job_id, 
                    previous_chunk, 
                    client_id, 
                    is_final=False
                )
                publish_duration = loop.time() - publish_start_time
                logger.debug(f"Job {job_id}: Published chunk to Redis in {publish_duration:.4f}s")
                full_response += previous_chunk
                has_sent_chunks = True
            previous_chunk = current_chunk_content

        # After the loop, handle the very last chunk (or empty stream)
        if previous_chunk is not None: 
            if not first_chunk_received: # Handle case where stream had only ONE chunk
                first_chunk_time = loop.time() - openai_call_start_time
                logger.info(f"Job {job_id}: Time to first (and only) chunk from OpenAI: {first_chunk_time:.4f}s")
            
            publish_start_time = loop.time()
            await publish_result_chunk(
                redis_conn,
                job_id,
                previous_chunk,
                client_id,
                is_final=True 
            )
            publish_duration = loop.time() - publish_start_time
            logger.info(f"Job {job_id}: Published FINAL chunk to Redis in {publish_duration:.4f}s")
            full_response += previous_chunk
            has_sent_chunks = True
        elif not has_sent_chunks: # Stream was empty
            if not first_chunk_received: # Log time to (non) first chunk if stream was empty
                first_chunk_time = loop.time() - openai_call_start_time
                logger.info(f"Job {job_id}: Time to (empty) response from OpenAI: {first_chunk_time:.4f}s")
            
            publish_start_time = loop.time()
            await publish_result_chunk(
                redis_conn,
                job_id,
                "", 
                client_id,
                is_final=True 
            )
            publish_duration = loop.time() - publish_start_time
            logger.info(f"Job {job_id}: Published FINAL empty chunk to Redis in {publish_duration:.4f}s")

        # 4. Save the complete assistant message
        db_save_start_time = loop.time()
        if full_response: 
            ai_message = Message(
                conversation_id=uuid.UUID(conversation_id),
                user_id=user_id,
                role="assistant",
                content=full_response,
                message_metadata={"completed": True}
            )
            db.add(ai_message)
            await db.commit()
            db_save_duration = loop.time() - db_save_start_time
            logger.info(f"Job {job_id}: Saved full response to DB in {db_save_duration:.4f}s")
            
            # 5. RACE CONDITION DETECTION: Check if response seems to lack context
            detect_race_condition_issues(conversation_id, message, context, full_response)
        else:
            logger.info(f"Job {job_id}: No content generated. Nothing to save to DB.")
        
        total_processing_duration = loop.time() - processing_start_time
        logger.info(f"Job {job_id}: Total processing time in worker (excluding ack): {total_processing_duration:.4f}s")
        return True
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
        # Capture error in Sentry with context
        sentry_sdk.capture_exception(e)
        # Publish an error chunk to the client
        error_message_for_client = f"[Error: Sorry, an unexpected error occurred while processing your reque st. Job ID: {job_id}]"
        await publish_result_chunk(
            redis_conn,
            job_id,
            error_message_for_client,
            client_id,
            is_final=True # Error is also a final state for this stream
        )
        # Optionally, save an error placeholder to DB or handle differently
        # For now, we are not saving OpenAI errors to the message history here,
        # only publishing to client.
        return False
    finally:
        await db.close()
        logger.info(f"Finished processing chat job {job_id}. DB session closed.")

async def worker_loop():
    """Main worker loop that processes jobs from Redis"""
    redis_conn = await get_redis_pool()
    
    # Register with consumer group
    logger.info(f"Worker {WORKER_ID} started in consumer group {CONSUMER_GROUP}")
    
    while not shutdown_event.is_set():
        try:
            # Read new messages from the stream using consumer group
            streams = await safe_redis_operation(
                redis_conn.xreadgroup,
                CONSUMER_GROUP,
                WORKER_ID,
                {LLM_JOBS_STREAM: ">"},  # > means "give me undelivered messages"
                count=1,
                block=5000  # Block for 5 seconds to reduce polling frequency
            )
            
            if not streams:
                # No new messages, try again
                continue
                
            _, messages = streams[0]
            
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
                await safe_redis_operation(redis_conn.xack, LLM_JOBS_STREAM, CONSUMER_GROUP, message_id)
                await safe_redis_operation(redis_conn.xdel, LLM_JOBS_STREAM, message_id)
                logger.info(f"Job {data.get('job_id', 'unknown')} completed and acknowledged")
            else:
                # Job failed
                if retry_count < MAX_RETRY_COUNT:
                    # Increment retry count and try again later
                    data["retry_count"] = str(retry_count + 1)
                    data["last_error_time"] = str(time.time())
                    
                    # Acknowledge current ID to remove from pending
                    await safe_redis_operation(redis_conn.xack, LLM_JOBS_STREAM, CONSUMER_GROUP, message_id)
                    
                    # Add back to stream with updated retry info
                    await safe_redis_operation(redis_conn.xadd, LLM_JOBS_STREAM, data)
                    
                    # Delete the original message
                    await safe_redis_operation(redis_conn.xdel, LLM_JOBS_STREAM, message_id)
                    
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
    
    try:
        # Claim pending jobs from Redis
        pending = await safe_redis_operation(redis_conn.xpending, LLM_JOBS_STREAM, CONSUMER_GROUP)
        
        if pending["pending"] > 0:
            logger.info(f"Found {pending['pending']} pending jobs from previous runs")
            
            # Get details on pending jobs
            pending_jobs = await safe_redis_operation(
                redis_conn.xpending_range,
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
                    claimed = await safe_redis_operation(
                        redis_conn.xclaim,
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
                                await safe_redis_operation(redis_conn.xack, LLM_JOBS_STREAM, CONSUMER_GROUP, msg_id)
                                await safe_redis_operation(redis_conn.xdel, LLM_JOBS_STREAM, msg_id)
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
    except Exception as e:
        logger.error(f"Error handling pending jobs: {str(e)}")

def handle_signals():
    """Set up signal handlers for graceful shutdown"""
    def signal_handler(signum, _):
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
            await safe_redis_operation(
                redis_conn.xgroup_create,
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

        # Check for pending jobs from previous runs
        await handle_pending_jobs()
        
        # Start worker loop
        await worker_loop()
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}", exc_info=True)
    finally:
        # Clean up Redis connection
        await close_redis_pool()
        logger.info("Worker shutdown complete")

if __name__ == "__main__":
    asyncio.run(main()) 