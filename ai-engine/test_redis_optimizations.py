#!/usr/bin/env python3
"""
Test script to validate Redis optimizations including:
1. Long-blocking reads
2. Connection pooling and health checks
3. Error handling with safe_redis_operation
"""
import asyncio
import logging
import time
import os
import sys
import argparse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("test_redis_optimizations")

# Parse command line arguments
parser = argparse.ArgumentParser(description="Test Redis optimizations")
parser.add_argument("--local", action="store_true", help="Use local Redis instance")
args = parser.parse_args()

# Set Redis URL to local if requested
if args.local:
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    logger.info("Using local Redis instance at redis://localhost:6379")

# Load environment variables
load_dotenv()

async def test_connection_and_safe_operations():
    """Test the Redis connection and safe operations wrapper"""
    from app.core.redis_client import get_redis_pool, safe_redis_operation
    
    logger.info("Testing Redis connection...")
    redis_conn = await get_redis_pool()
    
    try:
        # Test basic connection with ping
        result = await safe_redis_operation(redis_conn.ping)
        logger.info(f"Redis ping successful: {result}")
        
        # Test stream operations
        test_stream = "test_optimization_stream"
        
        # Clean up any existing test stream
        try:
            await safe_redis_operation(redis_conn.delete, test_stream)
            logger.info(f"Cleaned up existing test stream: {test_stream}")
        except Exception:
            pass
        
        # Test adding messages
        logger.info("Testing xadd operation...")
        msg_id = await safe_redis_operation(
            redis_conn.xadd,
            test_stream,
            {"key": "value", "timestamp": time.time()},
            id="*"
        )
        logger.info(f"Added message to stream with ID: {msg_id}")
        
        # Test reading with blocking
        logger.info("Testing xread with blocking (should return immediately)...")
        start_time = time.time()
        result = await safe_redis_operation(
            redis_conn.xread,
            streams={test_stream: "0-0"},
            count=1,
            block=5000
        )
        duration = time.time() - start_time
        logger.info(f"Blocking read completed in {duration:.4f}s with result: {result}")
        
        # Test reading with blocking when there are no new messages
        logger.info("Testing xread with blocking (should wait and timeout)...")
        start_time = time.time()
        result = await safe_redis_operation(
            redis_conn.xread,
            streams={test_stream: msg_id},
            count=1,
            block=2000  # 2 second timeout
        )
        duration = time.time() - start_time
        logger.info(f"Blocking read timed out after {duration:.4f}s with result: {result or 'None (timeout)'}")
        
        # Clean up
        await safe_redis_operation(redis_conn.delete, test_stream)
        logger.info(f"Cleaned up test stream: {test_stream}")
        
        logger.info("All Redis operations completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during Redis tests: {str(e)}")
        raise
    finally:
        # Close Redis connection
        await redis_conn.aclose()
        logger.info("Redis connection closed")

async def test_worker_optimizations():
    """Test worker optimizations including maintenance task"""
    from app.core.redis_client import run_maintenance_task
    
    logger.info("Testing worker-specific Redis optimizations...")
    
    # Test worker-0 logic (should run)
    os.environ["WORKER_ID"] = "worker-0"
    
    # Create a task for maintenance but cancel after 5 seconds
    maintenance_task = asyncio.create_task(run_maintenance_task())
    
    # Let it run for a short time
    logger.info("Started maintenance task, letting it run for 5 seconds...")
    await asyncio.sleep(5)
    
    # Cancel the task
    maintenance_task.cancel()
    try:
        await maintenance_task
    except asyncio.CancelledError:
        logger.info("Maintenance task cancelled as expected")
    
    # Test non-worker-0 logic (should skip)
    os.environ["WORKER_ID"] = "worker-1"
    
    # Create a task for maintenance but cancel after 2 seconds
    maintenance_task = asyncio.create_task(run_maintenance_task())
    
    # Let it run for a short time
    logger.info("Started maintenance task for worker-1, should skip...")
    await asyncio.sleep(2)
    
    # Cancel the task
    maintenance_task.cancel()
    try:
        await maintenance_task
    except asyncio.CancelledError:
        logger.info("Maintenance task cancelled")

async def main():
    """Run all tests"""
    logger.info("Starting Redis optimizations tests...")
    
    await test_connection_and_safe_operations()
    await test_worker_optimizations()
    
    logger.info("All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 