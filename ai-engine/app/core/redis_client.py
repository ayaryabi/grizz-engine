import os
import redis.asyncio as redis
import json
import logging
import asyncio
import time
from typing import Optional, Callable, Any
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Get Redis URL from environment, with fallback
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# Make URL secure for non-local connections
if REDIS_URL.startswith("redis://") and not REDIS_URL.startswith("redis://localhost"):
    REDIS_URL = REDIS_URL.replace("redis://", "rediss://", 1)
    logger.info("Using TLS for Redis connection")

# Redis stream names
LLM_JOBS_STREAM = "llm_jobs"
LLM_JOBS_DEAD = "llm_jobs_dead"  # Dead letter queue
RESULT_STREAM = "llm_results"

# Global connection pool
redis_pool = None

async def get_redis_pool() -> redis.Redis:
    """Get or create Redis connection pool"""
    global redis_pool
    if redis_pool is None:
        # Log without sensitive info
        safe_url = REDIS_URL.split("@")[-1] if "@" in REDIS_URL else REDIS_URL
        logger.info(f"Creating Redis connection pool to {safe_url}")
        
        # Set reasonable connection limit based on expected load
        worker_count = int(os.environ.get("WORKER_COUNT", "4"))
        api_instances = int(os.environ.get("API_INSTANCES", "1"))
        # Improved formula: workers*2 + api_instances + 10 for headroom
        max_connections = worker_count * 2 + api_instances + 10
        
        try:
            redis_pool = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                max_connections=max_connections,
                socket_timeout=5.0,           # Socket timeout
                socket_connect_timeout=5.0,   # Connection timeout
                retry_on_timeout=True,        # Auto-retry on timeout
                health_check_interval=30.0    # Regular health checks
            )
            
            # Create consumer groups if they don't exist
            try:
                await redis_pool.xgroup_create(
                    LLM_JOBS_STREAM, "llm_workers", mkstream=True, id="0"
                )
                logger.info("Created consumer group 'llm_workers' for stream 'llm_jobs'")
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.info("Consumer group 'llm_workers' already exists")
                else:
                    raise
                    
        except redis.RedisError as e:
            logger.error(f"Failed to create Redis connection pool: {str(e)}")
            # Re-raise to allow the application to handle failure
            raise
                
    return redis_pool

async def close_redis_pool():
    """Close Redis connection pool with proper cleanup"""
    global redis_pool
    if redis_pool:
        await redis_pool.aclose()  # Use aclose() to properly flush pending writes
        redis_pool = None
        logger.info("Redis connection pool closed")

async def trim_streams(redis_conn: Optional[redis.Redis] = None):
    """Trim streams to prevent them from growing too large"""
    if redis_conn is None:
        redis_conn = await get_redis_pool()
    
    try:
        # Keep reasonable number of entries
        await redis_conn.xtrim(LLM_JOBS_STREAM, maxlen=10000, approximate=True)
        await redis_conn.xtrim(RESULT_STREAM, maxlen=50000, approximate=True)
        await redis_conn.xtrim(LLM_JOBS_DEAD, maxlen=1000, approximate=True)
        logger.info("Trimmed Redis streams")
    except redis.RedisError as e:
        logger.error(f"Error trimming Redis streams: {str(e)}")

# Background task that runs periodic maintenance
async def run_maintenance_task():
    """Run a periodic task for Redis maintenance operations"""
    # Only run on worker-0 to avoid contention
    worker_id = os.environ.get("WORKER_ID", "")
    if worker_id != "worker-0":
        logger.info(f"Maintenance task skipped on {worker_id} (only runs on worker-0)")
        return
        
    logger.info(f"Starting Redis maintenance task on {worker_id}")
    
    while True:
        try:
            # Run every minute for stream trimming
            await asyncio.sleep(60)
            await trim_streams()
        except asyncio.CancelledError:
            logger.info("Redis maintenance task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in Redis maintenance task: {str(e)}")
            # Sleep a bit before retrying after an error
            await asyncio.sleep(5)

# Simple wrapper to handle Redis timeout and rate limit errors
async def safe_redis_operation(operation: Callable, *args, **kwargs) -> Any:
    """Execute a Redis operation with error handling"""
    try:
        return await operation(*args, **kwargs)
    except redis.TimeoutError as e:
        logger.error(f"Redis timeout error: {str(e)}")
        # Surface a user-friendly error
        raise ValueError("Server busy, please retry your request") from e
    except redis.ResponseError as e:
        if "max requests limit exceeded" in str(e).lower():
            logger.critical(f"Redis rate limit exceeded: {str(e)}")
            # This is a critical error that indicates we're beyond capacity
            raise ValueError("Service is currently at capacity, please try again later") from e
        # Let other response errors pass through
        raise 