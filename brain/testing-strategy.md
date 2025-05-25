# Grizz AI Engine - Testing Strategy
*Comprehensive testing plan for production-ready reliability*

## 🎯 **Executive Summary**

Our testing strategy focuses on **integration-first testing** to ensure the full chat flow works reliably under load. We'll test the complete pipeline from WebSocket → Redis Queue → LLM Workers → Database using **real environments** to catch issues before production.

**Goal**: Achieve 99%+ bug reduction and validate system capacity for 100+ concurrent users.

## 🏗️ **Testing Architecture Overview**

```
Client Simulation (Locust) → WebSocket → Redis Streams → LLM Workers → Database (Local Supabase)
                ↓
        Integration Tests (pytest)
                ↓  
         Unit Tests (individual components)
                ↓
       E2E Tests (full user flows)
```

## 🛠️ **Tools & Technologies**

### **Primary Testing Stack**
- **Supabase Local CLI**: Complete local PostgreSQL + Auth environment 
- **Locust**: Load testing with 100+ simulated users
- **pytest**: Unit and integration testing framework
- **pytest-asyncio**: Async test support
- **Playwright**: End-to-end browser testing
- **Docker**: Containerized testing environments

### **Supporting Tools**
- **pgTAP**: Database-level testing via Supabase CLI
- **Inbucket**: Email testing (built into Supabase local)
- **Redis**: Local Redis for queue testing
- **Mock servers**: OpenAI API mocking for cost control

## 📁 **Test Folder Structure**

```
ai-engine/
├── tests/
│   ├── unit/                 # Individual component tests
│   │   ├── test_redis_client.py
│   │   ├── test_queue_service.py
│   │   ├── test_llm_worker.py
│   │   └── test_openai_client.py
│   ├── integration/          # Multi-component flow tests
│   │   ├── test_chat_flow.py
│   │   ├── test_queue_to_worker.py
│   │   ├── test_websocket_redis.py
│   │   └── test_database_operations.py
│   ├── load/                 # Load and performance tests
│   │   ├── locustfile.py
│   │   ├── chat_simulation.py
│   │   └── stress_tests.py
│   ├── e2e/                  # End-to-end user journey tests
│   │   ├── test_user_chat_journey.py
│   │   ├── test_error_scenarios.py
│   │   └── test_auth_flows.py
│   └── fixtures/             # Shared test data and utilities
│       ├── test_users.py
│       ├── mock_responses.py
│       └── database_seeds.py
├── supabase/                 # Supabase local testing
│   ├── tests/database/       # pgTAP database tests
│   └── seed.sql             # Test data seeds
└── pytest.ini              # pytest configuration
```

## 🚀 **Implementation Priority Plan**

### **Phase 1: Integration Testing (Week 1) - HIGHEST PRIORITY** 🔥

**Why First**: Tests the real flow from `redis.md` - catches 80% of production issues

**Setup (Day 1)**:
- ✅ Supabase local environment (`npx supabase start`)
- ✅ Local Redis instance
- ✅ pytest configuration with async support

**Core Integration Tests (Days 2-3)**:
```python
# test_chat_flow.py - Test complete message flow
async def test_complete_chat_flow():
    # WebSocket message → Redis queue → Worker → Database → Response
    
# test_queue_to_worker.py - Test job processing  
async def test_job_processing_pipeline():
    # Queue job → Worker picks up → Processes → Acknowledges
    
# test_backpressure.py - Test system limits
async def test_backpressure_handling():
    # Queue 5000+ jobs → System should reject/throttle
```

**Load Testing (Days 4-5)**:
```python
# locustfile.py - 100 concurrent users
class ChatUser(User):
    @task
    async def send_chat_message():
        # Full WebSocket chat simulation
```

**Expected Results**: Know exact capacity limits and bottlenecks

### **Phase 2: Load Testing Optimization (Week 2) - HIGH PRIORITY** ⚡

**Focus**: Scale testing and performance validation

**Load Test Scenarios**:
- **Baseline**: 10 concurrent users (should be smooth)
- **Target Load**: 100 concurrent users (find breaking point)
- **Stress Test**: 500+ users (understand failure modes)
- **Burst Test**: Rapid message spikes

**Metrics to Track**:
- Response times (target: <5s per message)
- Queue depth growth 
- Database connection pool usage
- Redis operation rates
- Worker saturation points

### **Phase 3: Unit Testing (Week 3) - MEDIUM PRIORITY** 🧪

**Focus**: Individual component reliability

**Key Unit Tests**:
- Redis client connection handling
- Queue service backpressure logic
- LLM worker error recovery
- Database session management
- WebSocket connection lifecycle

### **Phase 4: E2E Testing (Week 4) - MEDIUM PRIORITY** 🎭

**Focus**: Full user journey validation

**E2E Scenarios**:
- New user registration → First chat → Response
- Multi-turn conversations
- Error handling (network failures, API errors)
- Authentication edge cases

## 🎮 **Testing Environments**

### **Local Development Testing**
```bash
# Start local Supabase
npx supabase start

# Configure AI engine for local testing
export DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
export SUPABASE_URL=http://localhost:54321

# Run integration tests
pytest tests/integration/ -v

# Run load tests
locust -f tests/load/locustfile.py --users 100
```

### **CI/CD Testing**
- GitHub Actions with Supabase local
- Automated integration tests on every PR
- Load test benchmarks on main branch
- Database migration testing

## 📊 **Success Metrics & Targets**

### **Performance Targets**
- **Response Time**: <5 seconds for 95% of messages
- **Throughput**: Handle 100 concurrent users
- **Queue Depth**: Stay below 1000 pending jobs under normal load
- **Error Rate**: <1% message processing failures

### **Reliability Targets** 
- **Uptime**: 99.9% availability
- **Data Integrity**: 0% message loss
- **Recovery Time**: <30 seconds after worker crashes

## 🔧 **Quick Start Commands**

```bash
# 1. Set up local testing environment (5 minutes)
npx supabase start
pip install pytest pytest-asyncio locust playwright

# 2. Run integration tests (validates core flow)
pytest tests/integration/test_chat_flow.py -v

# 3. Run load test (find capacity limits)
locust -f tests/load/locustfile.py --users 50 --spawn-rate 5

# 4. Run all tests
pytest tests/ --ignore=tests/load/

# 5. Clean up
npx supabase stop
```

## 🎯 **Expected Business Impact**

### **Risk Reduction**
- **90% fewer production bugs** (based on industry data)
- **Prevent system overload scenarios**
- **Validate scaling assumptions**

### **Development Speed**
- **Faster debugging** with comprehensive test coverage
- **Confident deployments** with integration validation
- **Clear capacity planning** with load test data

### **Cost Savings**
- **Prevent production outages** 
- **Reduce emergency fixes**
- **Optimize infrastructure** based on real usage data

## 🚨 **Critical Testing Scenarios**

### **Must Test Before Production**
1. **100 users sending messages simultaneously**
2. **OpenAI API rate limit handling**
3. **Redis connection pool exhaustion**
4. **Database session leaks**
5. **Worker crash recovery**
6. **WebSocket connection drops**

### **Edge Cases to Validate**
- Very long conversations (>50 messages)
- Rapid message bursts from single user
- Network interruptions mid-conversation
- Database maintenance scenarios
- Redis memory pressure

## ⏱️ **Timeline Summary**

- **Week 1**: Integration tests + Basic load testing → **Production confidence**
- **Week 2**: Advanced load testing → **Capacity planning**  
- **Week 3**: Unit tests → **Component reliability**
- **Week 4**: E2E tests → **User experience validation**

**Total Investment**: 4 weeks → **90% bug reduction + clear scaling roadmap**

This testing strategy ensures we can confidently handle hundreds of users while preventing the production issues that could damage user trust and business growth. 