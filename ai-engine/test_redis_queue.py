#!/usr/bin/env python3
"""
Test script for Redis queue integration.
"""
import asyncio
import json
import os
import sys
import time
import uuid
from dotenv import load_dotenv
import redis.asyncio as redis

# Load environment variables from .env file
load_dotenv()

# Redis connection details - Force local for testing
REDIS_URL = "redis://localhost:6379"
LLM_JOBS_STREAM = "llm_jobs"
RESULT_STREAM = "llm_results"
LLM_JOBS_DEAD = "llm_jobs_dead"

async def setup_test_environment():
    """Create necessary streams and groups"""
    r = redis.from_url(REDIS_URL, decode_responses=True)
    
    print(f"Connecting to Redis at {REDIS_URL.split('@')[-1]}")
    
    # Create streams and groups if they don't exist
    try:
        await r.xgroup_create(LLM_JOBS_STREAM, "llm_workers", mkstream=True, id="0")
        print(f"Created consumer group 'llm_workers' for stream '{LLM_JOBS_STREAM}'")
    except redis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group 'llm_workers' already exists")
        else:
            raise
            
    # Clean up any existing entries for the test
    await r.xtrim(LLM_JOBS_STREAM, maxlen=0)
    await r.xtrim(RESULT_STREAM, maxlen=0)
    await r.xtrim(LLM_JOBS_DEAD, maxlen=0)
    print("Cleared existing data from test streams")
    
    await r.aclose()
    
async def test_producer(job_count=5):
    """Simulate enqueueing multiple jobs"""
    r = redis.from_url(REDIS_URL, decode_responses=True)
    print(f"Producer: Creating {job_count} test jobs")
    
    for i in range(job_count):
        # Create a test job
        job_id = f"test-job-{uuid.uuid4()}"
        client_id = f"client:{uuid.uuid4()}"
        
        job_data = {
            "job_id": job_id,
            "type": "chat_completion",
            "user_id": "test-user",
            "conversation_id": f"test-convo-{i}",
            "message": f"Test message {i+1}",
            "metadata": json.dumps({"test": True, "client_id": client_id}),
            "timestamp": time.time(),
            "status": "pending"
        }
        
        # Add to Redis Stream
        message_id = await r.xadd(LLM_JOBS_STREAM, job_data)
        print(f"Added test job {job_id} with ID: {message_id}")
    
    # Trim the stream to prevent growth
    await r.xtrim(LLM_JOBS_STREAM, maxlen=100, approximate=True)
    
    # Close Redis connection
    await r.aclose()
    return job_count

async def test_consumer(consumer_id):
    """Simulate consuming jobs from the queue using consumer groups"""
    r = redis.from_url(REDIS_URL, decode_responses=True)
    
    print(f"Consumer {consumer_id} waiting for jobs...")
    processed = 0
    
    try:
        while True:
            # Read new messages from the stream using consumer group
            # This ensures each job is processed by only one consumer
            streams = await r.xreadgroup(
                "llm_workers",
                f"consumer-{consumer_id}",
                {LLM_JOBS_STREAM: ">"},  # > means "give me undelivered messages"
                count=1,
                block=5000
            )
            
            if not streams:
                print(f"Consumer {consumer_id}: No new messages, trying again...")
                continue
                
            stream_name, messages = streams[0]
            
            if not messages:
                print(f"Consumer {consumer_id}: No new messages, trying again...")
                continue
                
            message_id, data = messages[0]
            print(f"\nConsumer {consumer_id} received job: {message_id}")
            print(json.dumps(data, indent=2))
            
            # Extract client_id from metadata
            metadata = json.loads(data.get("metadata", "{}"))
            client_id = metadata.get("client_id", "unknown-client")
            
            # Simulate processing
            print(f"Consumer {consumer_id} processing job...")
            
            # Simulate responding with results
            for i in range(3):
                result = {
                    "job_id": data["job_id"],
                    "client_id": client_id,
                    "chunk": f"Response chunk {i+1} from consumer {consumer_id} for {data['message']}",
                    "is_final": "true" if i == 2 else "false",
                    "timestamp": time.time()
                }
                
                result_id = await r.xadd(RESULT_STREAM, result)
                print(f"Consumer {consumer_id} published result: {result_id}")
                await asyncio.sleep(0.5)
            
            # Acknowledge the message (mark as processed)
            await r.xack(LLM_JOBS_STREAM, "llm_workers", message_id)
            print(f"Consumer {consumer_id} acknowledged job {message_id}")
            
            processed += 1
            
            # Optionally exit after processing a certain number of jobs
            if processed >= 5:
                print(f"Consumer {consumer_id} processed {processed} jobs, exiting")
                break
                
            # Trim the results stream
            await r.xtrim(RESULT_STREAM, maxlen=100, approximate=True)
    
    except asyncio.CancelledError:
        print(f"Consumer {consumer_id} was cancelled after processing {processed} jobs")
        raise
    finally:
        await r.aclose()
        
    return processed

async def test_result_listener(client_id):
    """Test listening for results for a specific client"""
    r = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Last seen message ID
    last_id = "$"  # Start with new messages only
    
    print(f"Result listener started for client: {client_id}")
    
    try:
        for _ in range(30):  # Listen for 15 seconds (30 * 0.5s)
            # Read from the stream
            streams = await r.xread(
                streams={RESULT_STREAM: last_id},
                count=10,
                block=500  # 500ms timeout
            )
            
            if not streams:
                print("No new results yet...")
                await asyncio.sleep(0.5)
                continue
                
            stream_name, messages = streams[0]
            
            for message_id, data in messages:
                # Update last seen ID
                last_id = message_id
                
                # Extract data
                result_client_id = data.get("client_id", "")
                chunk = data.get("chunk", "")
                job_id = data.get("job_id", "")
                is_final = data.get("is_final") == "true"
                
                # Only show results for the requested client
                if result_client_id == client_id:
                    print(f"Received chunk for job {job_id}: {chunk}")
                    if is_final:
                        print(f"Final chunk received for job {job_id}")
                else:
                    print(f"Skipping result for different client: {result_client_id}")
    finally:
        await r.aclose()

async def test_multiconsumer():
    """Test having multiple consumers processing jobs"""
    # Start two consumer tasks
    consumer1 = asyncio.create_task(test_consumer(1))
    consumer2 = asyncio.create_task(test_consumer(2))
    
    # Wait a bit to let consumers connect
    await asyncio.sleep(1)
    
    # Choose a client ID to listen for results
    client_id = f"client:{uuid.uuid4()}"
    print(f"Using client_id for testing: {client_id}")
    
    # Add jobs that will send results to this client
    job_count = 10
    r = redis.from_url(REDIS_URL, decode_responses=True)
    
    for i in range(job_count):
        job_id = f"test-job-{uuid.uuid4()}"
        job_data = {
            "job_id": job_id,
            "type": "chat_completion",
            "user_id": "test-user",
            "conversation_id": f"test-convo-{i}",
            "message": f"Test message {i+1}",
            "metadata": json.dumps({"test": True, "client_id": client_id}),
            "timestamp": time.time(),
            "status": "pending"
        }
        message_id = await r.xadd(LLM_JOBS_STREAM, job_data)
        print(f"Added test job {job_id} with ID: {message_id}")
    
    await r.aclose()
    
    # Start a listener for the client results
    listener = asyncio.create_task(test_result_listener(client_id))
    
    # Let the system run for a while
    await asyncio.sleep(15)
    
    # Cancel all tasks
    for task in [consumer1, consumer2, listener]:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    # Verify stream state
    r = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Check if all jobs were processed
    jobs_info = await r.xinfo_stream(LLM_JOBS_STREAM)
    pending_count = jobs_info["length"] if "length" in jobs_info else 0
    
    # Check results
    results_info = await r.xinfo_stream(RESULT_STREAM)
    results_count = results_info["length"] if "length" in results_info else 0
    
    print(f"Remaining jobs in stream: {pending_count}")
    print(f"Result chunks in stream: {results_count}")
    
    # Clean up
    await r.xtrim(LLM_JOBS_STREAM, maxlen=0)
    await r.xtrim(RESULT_STREAM, maxlen=0)
    
    await r.aclose()
    
    if pending_count == 0:
        print("✅ Success: All jobs were processed!")
    else:
        print(f"⚠️ Warning: {pending_count} jobs were not processed.")

async def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print("Usage: python test_redis_queue.py [setup|producer|consumer|listener|multi|all]")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == "setup":
        await setup_test_environment()
    elif mode == "producer":
        job_count = 5
        if len(sys.argv) > 2:
            job_count = int(sys.argv[2])
        await test_producer(job_count)
    elif mode == "consumer":
        consumer_id = 1
        if len(sys.argv) > 2:
            consumer_id = int(sys.argv[2])
        await test_consumer(consumer_id)
    elif mode == "listener":
        client_id = f"client:{uuid.uuid4()}"
        if len(sys.argv) > 2:
            client_id = sys.argv[2]
        await test_result_listener(client_id)
    elif mode == "multi":
        await test_multiconsumer()
    elif mode == "all":
        print("=== Setting up test environment ===")
        await setup_test_environment()
        print("\n=== Running multi-consumer test ===")
        await test_multiconsumer()
    else:
        print("Invalid mode. Use 'setup', 'producer', 'consumer', 'listener', 'multi', or 'all'.")

if __name__ == "__main__":
    asyncio.run(main()) 