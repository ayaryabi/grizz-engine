#!/usr/bin/env python3
"""
Local test script for Redis optimizations that monitors operation count
"""
import asyncio
import logging
import time
import os
import argparse
import redis.asyncio as redis
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("redis_local_test")

# Load environment variables
load_dotenv()

# Command line arguments
parser = argparse.ArgumentParser(description="Test Redis optimizations locally")
parser.add_argument("--local", action="store_true", help="Use local Redis instance")
parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
parser.add_argument("--tabs", type=int, default=5, help="Number of simulated browser tabs")

# Global operation counter
operation_count = 0

# Simpler approach - use functions to count operations
async def count_operation(redis_conn, method_name, *args, **kwargs):
    """Count an operation and execute it"""
    global operation_count
    operation_count += 1
    
    # Get the method dynamically
    method = getattr(redis_conn, method_name)
    
    # Execute the method with the provided arguments
    return await method(*args, **kwargs)

async def simulate_old_polling(redis_conn, tab_id, duration=60):
    """Simulate the old aggressive polling approach"""
    logger.info(f"Tab {tab_id}: Starting old polling simulation for {duration} seconds")
    
    # Track operations for this tab
    tab_operations = 0
    start_time = time.time()
    
    # Use a dummy stream
    stream_key = f"test:old_polling:{tab_id}"
    last_id = "$"
    
    try:
        # Add a dummy message to start with
        await count_operation(redis_conn, "xadd", stream_key, {"msg": "initial"}, id="*")
        tab_operations += 1
        
        # Simulate polling until duration expires
        while time.time() - start_time < duration:
            # Old approach: Short polling (100ms)
            result = await count_operation(
                redis_conn, 
                "xread",
                streams={stream_key: last_id},
                count=10,
                block=100
            )
            tab_operations += 1
            
            # Wait 100ms between polls (simulating browser behavior)
            await asyncio.sleep(0.1)
            
            # If we got results, update last ID
            if result:
                stream_name, messages = result[0]
                last_id = messages[-1][0]
        
        # Cleanup
        await count_operation(redis_conn, "delete", stream_key)
        tab_operations += 1
        
        logger.info(f"Tab {tab_id}: Used {tab_operations} Redis operations in {duration} seconds")
        return tab_operations
    
    except Exception as e:
        logger.error(f"Error in old polling simulation: {str(e)}")
        return 0

async def simulate_new_blocking(redis_conn, tab_id, duration=60):
    """Simulate the new long-blocking approach"""
    logger.info(f"Tab {tab_id}: Starting new blocking simulation for {duration} seconds")
    
    # Track operations for this tab
    tab_operations = 0
    start_time = time.time()
    
    # Use a dummy stream
    stream_key = f"test:new_blocking:{tab_id}"
    last_id = "$"
    
    try:
        # Add a dummy message to start with
        await count_operation(redis_conn, "xadd", stream_key, {"msg": "initial"}, id="*")
        tab_operations += 1
        
        # Simulate blocking reads until duration expires
        while time.time() - start_time < duration:
            # New approach: Long blocking (15 seconds)
            result = await count_operation(
                redis_conn,
                "xread",
                streams={stream_key: last_id},
                count=20,
                block=15000
            )
            tab_operations += 1
            
            # If we got results, update last ID
            if result:
                stream_name, messages = result[0]
                last_id = messages[-1][0]
        
        # Cleanup
        await count_operation(redis_conn, "delete", stream_key)
        tab_operations += 1
        
        logger.info(f"Tab {tab_id}: Used {tab_operations} Redis operations in {duration} seconds")
        return tab_operations
    
    except Exception as e:
        logger.error(f"Error in new blocking simulation: {str(e)}")
        return 0

async def test_idle_connections():
    """Test Redis operations with idle connections"""
    args = parser.parse_args()
    
    # Setup Redis connection
    if args.local:
        redis_url = "redis://localhost:6379"
        logger.info("Using local Redis instance")
    else:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        logger.info(f"Using Redis URL from environment: {redis_url.split('@')[-1]}")
    
    redis_conn = redis.from_url(redis_url, decode_responses=True)
    
    try:
        # First test old polling with multiple tabs
        logger.info(f"=== Testing OLD polling with {args.tabs} tabs for {args.duration} seconds ===")
        global operation_count
        operation_count = 0
        
        # Start old polling tasks
        old_tasks = [
            asyncio.create_task(
                simulate_old_polling(redis_conn, i, args.duration)
            )
            for i in range(args.tabs)
        ]
        
        # Wait for all tasks to complete
        old_results = await asyncio.gather(*old_tasks)
        old_total = sum(old_results)
        old_ops_per_tab = old_total / args.tabs
        old_ops_per_second_per_tab = old_ops_per_tab / args.duration
        
        logger.info(f"=== OLD Polling Results: ===")
        logger.info(f"Total operations: {old_total}")
        logger.info(f"Operations per tab: {old_ops_per_tab:.2f}")
        logger.info(f"Operations per second per tab: {old_ops_per_second_per_tab:.2f}")
        logger.info(f"Projected operations per day per tab: {old_ops_per_second_per_tab * 86400:.2f}")
        
        # Let Redis settle between tests
        await asyncio.sleep(2)
        
        # Now test new blocking with multiple tabs
        logger.info(f"=== Testing NEW blocking with {args.tabs} tabs for {args.duration} seconds ===")
        operation_count = 0
        
        # Start new blocking tasks
        new_tasks = [
            asyncio.create_task(
                simulate_new_blocking(redis_conn, i, args.duration)
            )
            for i in range(args.tabs)
        ]
        
        # Wait for all tasks to complete
        new_results = await asyncio.gather(*new_tasks)
        new_total = sum(new_results)
        new_ops_per_tab = new_total / args.tabs
        new_ops_per_second_per_tab = new_ops_per_tab / args.duration
        
        logger.info(f"=== NEW Blocking Results: ===")
        logger.info(f"Total operations: {new_total}")
        logger.info(f"Operations per tab: {new_ops_per_tab:.2f}")
        logger.info(f"Operations per second per tab: {new_ops_per_second_per_tab:.2f}")
        logger.info(f"Projected operations per day per tab: {new_ops_per_second_per_tab * 86400:.2f}")
        
        # Calculate improvement
        reduction_percent = 100 * (old_total - new_total) / old_total if old_total > 0 else 0
        logger.info(f"=== Improvement: {reduction_percent:.2f}% reduction in Redis operations ===")
        
        # Extrapolate to 1000 users with browser open for 8 hours
        old_projected = old_ops_per_second_per_tab * 1000 * 8 * 3600
        new_projected = new_ops_per_second_per_tab * 1000 * 8 * 3600
        
        logger.info(f"\n=== Production Projection ===")
        logger.info(f"OLD approach - 1000 users with browser open for 8 hours: {old_projected:,.0f} operations")
        logger.info(f"NEW approach - 1000 users with browser open for 8 hours: {new_projected:,.0f} operations")
        
    finally:
        # Clean up
        await redis_conn.aclose()

async def run_test():
    """Main entry point"""
    logger.info("Starting Redis optimization local test")
    await test_idle_connections()
    logger.info("Test completed!")

if __name__ == "__main__":
    asyncio.run(run_test()) 