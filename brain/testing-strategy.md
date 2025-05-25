# Grizz AI Engine - Testing Strategy
*Comprehensive testing plan for production-ready reliability*

## 🎯 **Executive Summary**

Our testing strategy focuses on **testing the ACTUAL running system** to ensure the full chat flow works reliably under load. Tests call your **real WebSocket endpoints, Redis operations, and database functions** - not recreated test code.

**Key Principle**: Tests connect to your **actual running AI engine** to verify real system behavior.

**Goal**: Achieve 90%+ bug reduction and validate system capacity for 100+ concurrent users.

## 🏗️ **How Testing Actually Works**

### **❌ WRONG: Tests Don't Recreate Your Code**
```python
# DON'T DO THIS - Manually implementing Redis in tests
await redis_client.xadd("llm_jobs", job_data)  # ❌ Recreating queue logic
```

### **✅ CORRECT: Tests Call Your Real Running System**
```python
# DO THIS - Test your actual AI engine
async with websockets.connect("ws://localhost:8000/ws/chat/test?token=jwt") as ws:
    await ws.send("Hello!")  # Calls YOUR ws.py WebSocket handler
    response = await ws.recv()  # Gets response from YOUR complete system
    assert len(response) > 0   # Verifies YOUR system works
```

### **What's Actually Running During Tests:**
```bash
Terminal 1: npx supabase start        # Real PostgreSQL + Auth
Terminal 2: redis-server              # Real Redis
Terminal 3: python launcher.py        # YOUR actual AI engine
Terminal 4: pytest tests/integration/ # Tests calling YOUR endpoints
```

## 🛠️ **Tools & Technologies**

### **Primary Testing Stack**
- **Supabase Local CLI**: Real PostgreSQL + Auth environment locally
- **Redis Server**: Real Redis instance for queue testing
- **pytest**: Test runner that calls your actual code
- **pytest-asyncio**: Async test support for WebSocket testing
- **Locust**: Load testing against your real running system
- **websockets**: Python library to connect to your real WebSocket endpoints

### **Supporting Tools**
- **pgTAP**: Database-level testing via Supabase CLI
- **Inbucket**: Email testing (built into Supabase local)
- **Docker**: Optional containerized testing environments

## 📁 **Corrected Test Folder Structure**

```
ai-engine/
├── tests/
│   ├── integration/          # Multi-component flow tests (functional)
│   │   ├── flows/
│   │   │   ├── test_message_flow.py      # WebSocket → Redis → Worker → DB
│   │   │   ├── test_queue_flow.py        # Redis streams + consumer groups
│   │   │   └── test_result_flow.py       # Result streaming back
│   │   ├── resilience/
│   │   │   ├── test_backpressure.py      # System limits (functional)
│   │   │   └── test_worker_recovery.py   # Error recovery logic
│   │   └── conversations/
│   │       └── test_multi_turn_chat.py   # Conversation context logic
│   ├── load/                 # Performance & scale testing
│   │   ├── locustfile.py                 # Main load testing (100+ users)
│   │   ├── test_burst_traffic.py         # Sudden traffic spikes
│   │   ├── test_concurrent_users.py      # Multiple users simultaneously
│   │   └── test_capacity_limits.py       # Find breaking points
│   ├── unit/                 # Individual component tests
│   │   ├── test_redis_client.py
│   │   ├── test_queue_service.py
│   │   ├── test_llm_worker.py
│   │   └── test_openai_client.py
│   └── fixtures/             # Shared test utilities
│       ├── test_users.py
│       ├── mock_responses.py
│       └── database_seeds.py
├── supabase/                 # Supabase local testing
│   ├── tests/database/       # pgTAP database tests
│   └── seed.sql             # Test data seeds
└── pytest.ini              # pytest configuration
```

## 🔄 **Integration vs Load Tests - Key Difference**

### **Integration Tests** (Functional Verification)
- **Purpose**: Verify components work together correctly
- **Scale**: 1-5 simulated users
- **Goal**: "Does the logic work end-to-end?"
- **Example**: Send one message → verify it flows through all components correctly
- **Tools**: pytest calling your real WebSocket endpoints

### **Load Tests** (Performance & Capacity)
- **Purpose**: Find system limits and performance characteristics  
- **Scale**: 10-1000+ simulated users
- **Goal**: "How many users can we handle?"
- **Example**: 100 users sending messages → find breaking point
- **Tools**: Locust hitting your real running system

## 🚀 **Implementation Priority Plan**

### **Phase 1: Environment Setup + Basic Integration (Day 1) - HIGHEST PRIORITY** 🔥

**Setup Real Services (30 minutes)**:
```bash
# 1. Start Supabase local (PostgreSQL + Auth)
npx supabase start

# 2. Start Redis
redis-server --port 6379

# 3. Configure your AI engine for testing
export DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
export REDIS_URL=redis://localhost:6379
export ENVIRONMENT=test

# 4. Start YOUR actual AI engine
python launcher.py --workers 2
```

**Basic Integration Test (1 hour)**:
```python
# tests/integration/flows/test_message_flow.py
@pytest.mark.asyncio
async def test_complete_chat_flow():
    """Test YOUR actual running system end-to-end"""
    
    # Connect to YOUR WebSocket endpoint
    uri = "ws://localhost:8000/ws/chat/test-conv?token=test-jwt"
    
    async with websockets.connect(uri) as websocket:
        # Send message through YOUR system
        await websocket.send("Hello, integration test!")
        
        # YOUR code handles: WebSocket → Redis → Worker → OpenAI → Response
        response_chunks = []
        for _ in range(10):  # Collect response chunks
            try:
                chunk = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_chunks.append(chunk)
            except asyncio.TimeoutError:
                break
        
        # Verify YOUR system worked
        assert len(response_chunks) > 0, "No response from YOUR system"
```

**Expected Results**: Know your current system works end-to-end

### **Phase 2: Load Testing (Day 2-3) - HIGH PRIORITY** ⚡

**Basic Load Test (2 hours)**:
```python
# tests/load/locustfile.py
from locust import User, task, between
import asyncio
import websockets

class ChatUser(User):
    wait_time = between(1, 3)
    
    @task
    async def send_chat_message(self):
        """Load test YOUR actual WebSocket endpoint"""
        
        uri = f"ws://localhost:8000/ws/chat/test-{self.user_id}?token=test-jwt"
        
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(f"Hello from user {self.user_id}!")
                
                # Wait for response from YOUR system
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                
                # Record success (YOUR system responded)
                self.environment.events.request.fire(
                    request_type="WebSocket",
                    name="chat_message", 
                    response_time=100,  # Measure actual response time
                    exception=None
                )
        except Exception as e:
            # Record failure (YOUR system failed)
            self.environment.events.request.fire(
                request_type="WebSocket",
                name="chat_message",
                response_time=0,
                exception=e
            )
```

**Run Load Tests**:
```bash
# Start with small load
locust -f tests/load/locustfile.py --users 10 --spawn-rate 2 --host ws://localhost:8000

# Scale up to find limits
locust -f tests/load/locustfile.py --users 100 --spawn-rate 5 --host ws://localhost:8000
```

### **Phase 3: Component Integration Tests (Week 2) - MEDIUM PRIORITY** 🧪

**Test Your Real Components Working Together**:
```python
# tests/integration/flows/test_queue_flow.py
@pytest.mark.asyncio
async def test_your_queue_system():
    """Test YOUR actual queue_service.py functions"""
    
    # Import YOUR actual functions
    from app.services.queue_service import queue_chat_message
    from app.core.queue import get_pending_job_count
    
    # Call YOUR real queue function
    job_id = await queue_chat_message(
        user_id="test-user",
        conversation_id="test-conv",
        message="Test YOUR queue",
        client_id="test-client"
    )
    
    # Verify YOUR function worked
    pending_count = await get_pending_job_count()
    assert pending_count > 0, "YOUR queue function failed"
```

### **Phase 4: Edge Cases & Resilience (Week 3) - MEDIUM PRIORITY** 🎭

**Test YOUR System Under Stress**:
```python
# tests/integration/resilience/test_backpressure.py
@pytest.mark.asyncio
async def test_your_backpressure_system():
    """Test YOUR actual backpressure thresholds"""
    
    # Import YOUR actual backpressure function
    from app.core.queue import check_backpressure
    
    # Test YOUR 3000/5000 job limits
    # (Add jobs to YOUR Redis instance and test YOUR function)
```

## 🎮 **Practical Testing Environment**

### **Required Services Running**
```bash
# These MUST be running for tests to work:

# 1. PostgreSQL (via Supabase local)
npx supabase start  # Gives you localhost:54322

# 2. Redis 
redis-server --port 6379  # Or: docker run -p 6379:6379 redis:alpine

# 3. YOUR AI Engine
python launcher.py --workers 2  # YOUR actual system

# 4. Run tests against YOUR running system
pytest tests/integration/ -v
locust -f tests/load/locustfile.py --users 50
```

### **Test Configuration**
```python
# tests/conftest.py
import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configure tests to use YOUR local services"""
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:54322/postgres"
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["SUPABASE_URL"] = "http://localhost:54321"
    os.environ["ENVIRONMENT"] = "test"

@pytest.fixture
async def redis_client():
    """Connect to YOUR Redis instance"""
    from app.core.redis_client import get_redis_pool
    client = await get_redis_pool()
    yield client
    # Clean up test data
    await client.flushdb()
```

## 📊 **Success Metrics & Targets**

### **Integration Test Success**
- ✅ **Message flow works**: WebSocket → Redis → Worker → Database → Response
- ✅ **Queue processing works**: Jobs queued and processed correctly
- ✅ **Error handling works**: System recovers from failures gracefully
- ✅ **Multi-turn conversations work**: Context maintained across messages

### **Load Test Targets**
- **Response Time**: <5 seconds for 95% of messages under normal load
- **Throughput**: Handle 100 concurrent users without errors
- **Queue Depth**: Stay below 1000 pending jobs under normal load  
- **Error Rate**: <1% message processing failures

### **System Resilience**
- **Backpressure**: System rejects requests when overloaded (>5000 jobs)
- **Recovery**: Workers restart and process pending jobs after crashes
- **Connection Handling**: Redis/DB connections properly managed under load

## 🔧 **Quick Start Commands**

```bash
# 1. Set up testing environment (5 minutes)
npx supabase start
redis-server &
pip install pytest pytest-asyncio locust websockets

# 2. Start YOUR system
export DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
export REDIS_URL=redis://localhost:6379
python launcher.py --workers 2

# 3. Run integration tests (tests YOUR actual system)
pytest tests/integration/test_message_flow.py -v

# 4. Run load test (stress YOUR actual system)
locust -f tests/load/locustfile.py --users 20 --spawn-rate 2

# 5. Clean up
npx supabase stop
```

## 🎯 **Why This Approach Works**

### **✅ Tests Real System Behavior**
- Tests call YOUR actual WebSocket endpoints
- Tests use YOUR actual Redis operations
- Tests verify YOUR actual database operations
- **If tests pass → YOUR real system definitely works!**

### **✅ Catches Real Integration Issues**
- Component interaction bugs
- Performance bottlenecks under load
- Race conditions in concurrent scenarios
- Configuration issues

### **✅ Provides Confidence for Production**
- Know exact capacity limits
- Validated error handling
- Proven system resilience
- Real performance characteristics

## ⏱️ **Timeline Summary**

- **Day 1**: Basic integration test → **YOUR system works end-to-end**
- **Day 2-3**: Load testing → **Know YOUR capacity limits**  
- **Week 2**: Component integration → **YOUR components work together**
- **Week 3**: Resilience testing → **YOUR system handles edge cases**

**Total Investment**: 3 weeks → **90% bug reduction + validated system capacity**

This testing strategy ensures you can confidently deploy YOUR actual system to production, knowing it has been thoroughly tested under real conditions. 