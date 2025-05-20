import os
import redis.asyncio as redis
import json
import logging
import asyncio
from typing import Optional
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
        max_connections = worker_count * 2 + 5  # Workers + web servers + margin
        
        redis_pool = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            max_connections=max_connections
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
    
    # Keep reasonable number of entries
    await redis_conn.xtrim(LLM_JOBS_STREAM, maxlen=10000, approximate=True)
    await redis_conn.xtrim(RESULT_STREAM, maxlen=50000, approximate=True)
    await redis_conn.xtrim(LLM_JOBS_DEAD, maxlen=1000, approximate=True)
    logger.info("Trimmed Redis streams")

async def schedule_maintenance():
    """Run maintenance tasks periodically"""
    while True:
        await asyncio.sleep(3600)  # Every hour
        try:
            await trim_streams()
        except Exception as e:
            logger.error(f"Error in Redis maintenance: {str(e)}") 