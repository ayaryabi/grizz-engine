import asyncio
import logging
import sys
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import after environment is loaded
from app.db.database import async_session_maker
from sqlalchemy import text

# Number of concurrent workers
CONCURRENCY = 200
# Number of queries per worker
QUERIES_PER_WORKER = 5

async def worker(worker_id):
    """Run a database worker that executes a simple query multiple times"""
    try:
        async with async_session_maker() as session:
            for i in range(QUERIES_PER_WORKER):
                # Execute a simple query
                result = await session.execute(text("SELECT 1"))
                value = result.scalar_one()
                # Uncomment for verbose logs (will generate a lot of output)
                # logger.debug(f"Worker {worker_id}, query {i}: result = {value}")
            return True
    except Exception as e:
        logger.error(f"Worker {worker_id} failed: {str(e)}")
        return False

async def test_concurrency_burst():
    """Run a concurrency test with multiple simultaneous database connections"""
    logger.info(f"Starting concurrency burst test with {CONCURRENCY} workers")
    
    start_time = time.time()
    
    # Create and gather all worker tasks
    tasks = []
    for i in range(CONCURRENCY):
        tasks.append(asyncio.create_task(worker(i)))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Calculate success rate and elapsed time
    elapsed = time.time() - start_time
    success_count = sum(1 for result in results if result is True)
    failure_count = CONCURRENCY - success_count
    
    logger.info(f"Concurrency test completed in {elapsed:.2f} seconds")
    logger.info(f"Success: {success_count}/{CONCURRENCY} workers ({success_count/CONCURRENCY*100:.1f}%)")
    
    if failure_count > 0:
        logger.error(f"Failed: {failure_count}/{CONCURRENCY} workers")
        # Analyze failure types
        error_types = {}
        for result in results:
            if isinstance(result, Exception):
                error_type = type(result).__name__
                error_types[error_type] = error_types.get(error_type, 0) + 1
        logger.error(f"Error types: {error_types}")
    
    # Calculate queries per second
    total_queries = CONCURRENCY * QUERIES_PER_WORKER
    qps = total_queries / elapsed
    logger.info(f"Processed {total_queries} queries ({qps:.1f} queries/sec)")
    
    # Test passes if at least 95% of workers succeeded
    success_rate = success_count / CONCURRENCY
    return success_rate >= 0.95

if __name__ == "__main__":
    success = asyncio.run(test_concurrency_burst())
    if success:
        print("✅ Concurrency burst test passed!")
        sys.exit(0)
    else:
        print("❌ Concurrency burst test failed!")
        sys.exit(1) 