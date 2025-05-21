# Redis Optimization Summary

## Overview

We've implemented substantial optimizations to the Redis usage in the Grizz Engine, focusing on reducing the number of Redis operations, improving connection management, and enhancing resilience. These changes should reduce Redis usage by approximately 90% in idle conditions and significantly improve overall system stability.

## Optimizations Implemented

### 1. Long-Blocking XREAD

**File**: `queue_service.py`

- **Before**: Polling every 100ms regardless of activity 
- **After**: Using XREAD with 15-second blocking timeout
- **Impact**: Reduces polling operations from ~10/second to ~4/minute (a 99% reduction for idle connections)

```python
# Before:
streams = await redis_conn.xread(
    streams={RESULT_STREAM: last_id},
    count=10,
    block=100  # Check every 100ms
)

# After:
streams = await safe_redis_operation(
    redis_conn.xread,
    streams={RESULT_STREAM: last_id},
    count=20,  # Process more messages at once
    block=15000  # Block for up to 15 seconds
)
```

### 2. Optimized Connection Pool Management

**File**: `redis_client.py`

- Added proper connection limits based on worker count and API instances
- Added socket timeouts (5 seconds) to prevent hanging connections
- Added health checks every 30 seconds to detect dead connections
- Improved error handling with the `safe_redis_operation` wrapper

```python
redis_pool = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=max_connections,
    socket_timeout=5.0,           # Socket timeout
    socket_connect_timeout=5.0,   # Connection timeout
    retry_on_timeout=True,        # Auto-retry on timeout
    health_check_interval=30.0    # Regular health checks
)
```

### 3. Idle WebSocket Connection Management

**File**: `ws.py`

- Added tracking of last activity time on WebSocket connections
- Automatically closes idle connections after 5 minutes of inactivity
- Uses proper WebSocket close codes (1000 and 1001) for browser compatibility

```python
# Check if connection is idle for more than 5 minutes (300s)
idle_seconds = time.time() - last_activity_time
if idle_seconds > 300:
    logger.info(f"Closing idle WebSocket connection after {idle_seconds:.1f}s of inactivity")
    # Use code 1000 (normal closure) so browsers don't treat it as an error
    await websocket.close(code=1000)
```

### 4. Redis Stream Maintenance

**Files**: `redis_client.py`, `launcher.py`, `queue.py`

- Created a dedicated maintenance task that runs only on worker-0
- Runs every 60 seconds to trim Redis streams to reasonable sizes
- Removed wasteful trimming operations that were running on every job
- Added proper error handling for maintenance operations

```python
# Only runs on worker-0 to avoid contention between workers
worker_id = os.environ.get("WORKER_ID", "")
if worker_id != "worker-0":
    logger.info(f"Maintenance task skipped on {worker_id} (only runs on worker-0)")
    return
```

### 5. Error Handling and Rate Limit Protection

**Files**: Across all Redis-using components

- Added the `safe_redis_operation` wrapper for all Redis operations
- Gracefully handles timeouts and rate limit errors
- Provides user-friendly error messages when Redis limits are hit
- Prevents cascading failures during Redis outages

```python
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
```

## Expected Impact

Based on our analysis and the implemented changes:

1. **Idle Connections**: Reduced from ~9 operations/second to ~4 operations/minute per tab
   - Before: A single browser tab left open overnight would use ~500K Redis operations
   - After: A single browser tab left open overnight will use ~2.5K Redis operations (99.5% reduction)

2. **Connection Management**: 
   - Automatic cleanup of idle connections will free up server resources
   - Proper health checks prevent "zombie" connections
   - Controlled connection pool size prevents connection explosions

3. **System Stability**:
   - Proper timeout handling prevents hanging requests
   - Rate limit and backpressure detection prevents cascading failures
   - Worker-specific maintenance prevents contention

## Next Steps

Despite our optimizations, we recommend a few additional improvements for future implementation:

1. **Pub/Sub Implementation**: Consider replacing XREAD with Pub/Sub for result streaming in the future for even better performance

2. **Redis Cluster Upgrade**: As the system scales, consider upgrading to a paid tier of Upstash or a self-hosted Redis cluster

3. **Circuit Breaker Pattern**: Implement a full circuit breaker around Redis operations to gracefully degrade during Redis outages

4. **Load Testing**: Perform thorough load testing to validate our optimizations:
   - Test with 100+ concurrent users
   - Test with long idle periods
   - Test with rapid message sequences

5. **Monitoring**: Add Redis-specific metrics to the monitoring system:
   - Operations per second
   - Connection counts
   - Queue depths

## Conclusion

These optimizations have transformed the Redis usage pattern from an aggressive polling model to an efficient blocking-read approach, dramatically reducing the number of operations while maintaining responsiveness. The system should now be able to handle thousands of concurrent users within the free tier limits of Upstash Redis. 