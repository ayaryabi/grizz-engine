#!/usr/bin/env python3
"""
Bulletproof Async Database Tests

This script runs all async database tests in sequence to verify that the database layer
is production-ready according to the criteria in the architecture document.

Usage: python test_db_bulletproof.py
"""

import asyncio
import sys
import time
import logging
from dotenv import load_dotenv
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import test modules
from test_async_db import test_async_db
from test_read_write import test_real_table_operations
from test_concurrency import test_concurrency_burst

async def run_all_tests():
    """Run all async database tests in sequence"""
    start_time = time.time()
    results = {}
    
    logger.info("🚀 Starting Bulletproof Database Tests")
    logger.info("======================================")
    
    # Basic async operations test
    logger.info("\n📋 BASIC ASYNC OPERATIONS TEST:")
    try:
        basic_result = await test_async_db()
        results["basic_operations"] = "✅ PASSED" if basic_result else "❌ FAILED"
        logger.info(f"Basic operations test: {results['basic_operations']}")
    except Exception as e:
        logger.error(f"Error in basic operations test: {str(e)}")
        logger.error(traceback.format_exc())
        results["basic_operations"] = "❌ FAILED"
    
    # Real table write/read test
    logger.info("\n📋 REAL TABLE WRITE & READ-BACK TEST:")
    try:
        write_read_result = await test_real_table_operations()
        results["write_read"] = "✅ PASSED" if write_read_result else "❌ FAILED"
        logger.info(f"Real table write/read test: {results['write_read']}")
    except Exception as e:
        logger.error(f"Error in real table write/read test: {str(e)}")
        logger.error(traceback.format_exc())
        results["write_read"] = "❌ FAILED"
    
    # Concurrency burst test
    logger.info("\n📋 CONCURRENCY BURST TEST:")
    try:
        concurrency_result = await test_concurrency_burst()
        results["concurrency"] = "✅ PASSED" if concurrency_result else "❌ FAILED"
        logger.info(f"Concurrency burst test: {results['concurrency']}")
    except Exception as e:
        logger.error(f"Error in concurrency burst test: {str(e)}")
        logger.error(traceback.format_exc())
        results["concurrency"] = "❌ FAILED"
    
    # Report overall results
    elapsed = time.time() - start_time
    logger.info("\n📊 TEST RESULTS SUMMARY:")
    logger.info("=====================")
    for test_name, result in results.items():
        logger.info(f"{test_name}: {result}")
    
    all_passed = all(result == "✅ PASSED" for result in results.values())
    logger.info(f"\n⏱️ Total test time: {elapsed:.2f} seconds")
    
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED! The database layer is bulletproof and production-ready.")
        return True
    else:
        logger.info("\n❗ SOME TESTS FAILED. Review the logs and fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1) 