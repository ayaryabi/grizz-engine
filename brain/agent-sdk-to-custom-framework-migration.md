# Agent SDK to Custom Framework Migration Plan

## 🎯 **Executive Summary**

**Current Problem**: Agent SDK performance inconsistency (5s to 42s for same task)  
**Solution**: Build lightweight custom framework using existing orchestration logic  
**Effort**: ~3-4 days (200 lines of new code + testing)  
**Result**: Consistent performance + reusable framework for future agents

---

## 📊 **Performance Analysis Results**

### Current Agent SDK Issues
- **Inconsistent timing**: 5s → 42s for identical tasks
- **Unknown bottlenecks**: Can't debug Agent SDK internals  
- **Server dependency**: Performance varies with OpenAI's Agent SDK servers
- **Limited control**: Cannot optimize execution flow

### Test Results Summary
```
Direct OpenAI API:     6-7s (consistent)
Agent SDK:            5-42s (unpredictable)
Current Parallelization: ✅ Working (2 steps in parallel)
Redis Optimization:   ✅ Working (hash-based state)
```

---

## 🏗️ **What We Already Have (90% Complete)**

### ✅ **Core Components Ready**
1. **Orchestration Engine**: `RedisWorkflowOrchestrator.execute_workflow()`
   - Dependency resolution logic
   - Parallel execution with `asyncio.gather()`
   - Redis state management
   - Error handling & timing

2. **Data Models**: Perfect Pydantic structures
   - `MemoryPlan`, `PlanStep` 
   - `MemoryExecutionResult`
   - All tool input/output models

3. **Tool Infrastructure**: `@function_tool` pattern
   - All memory tools working
   - Redis-based state passing
   - Parallel-safe execution

4. **Redis Integration**: Production-ready
   - `get_redis_pool()` 
   - Hash-based workflows
   - State persistence

### ✅ **Proven Patterns**
- Direct OpenAI API calls (from `test_direct_openai.py`)
- Structured output with Pydantic models
- Dependency-based parallel execution
- Redis workflow orchestration

---

## 🔧 **What Needs Building (10% Remaining)**

### **1. CustomAgent Class** (~50 lines)
```python
class CustomAgent:
    def __init__(self, name, instructions, output_type, model, tools)
    async def run(self, input_text) -> structured_output
    # Uses direct OpenAI API + structured output
```

### **2. CustomRunner Class** (~100 lines)  
```python
class CustomRunner:
    async def execute_plan(self, plan, tool_registry)
    # Generalized version of current execute_workflow()
```

### **3. ToolRegistry Class** (~50 lines)
```python
class ToolRegistry:
    def register(self, name, func)
    async def call_tool(self, name, **kwargs)
    # Centralized tool management
```

---

## 📋 **Migration Plan (4 Phases)**

### **Phase 1: Extract & Generalize** (Day 1 - 4 hours)
**Goal**: Create reusable framework from existing code

**Steps**:
1. Create `app/framework/` directory
2. Extract orchestration logic from `RedisWorkflowOrchestrator`
3. Generalize for any plan type (not just MemoryPlan)
4. Create `CustomAgent`, `CustomRunner`, `ToolRegistry` classes
5. Copy proven OpenAI API pattern from `test_direct_openai.py`

**Output**: Working custom framework (untested)

### **Phase 2: Replace Memory System** (Day 2 - 6 hours)
**Goal**: Migrate memory agents to custom framework

**Steps**:
1. Create `CustomMemoryPlannerAgent` (replaces Agent SDK planner)
2. Create `CustomMemoryActorAgent` (replaces Agent SDK actor)
3. Update `MemoryManager` to use custom agents
4. Keep all existing tools & Redis logic unchanged
5. Run `test_redis_memory.py` for validation

**Output**: Memory system on custom framework

### **Phase 3: Test & Optimize** (Day 3 - 4 hours)
**Goal**: Ensure performance gains & stability

**Steps**:
1. Performance comparison tests (old vs new)
2. Stress testing with various content sizes
3. Error handling validation
4. Parallel execution verification
5. Redis state consistency checks

**Output**: Production-ready memory system

### **Phase 4: Documentation & Reusability** (Day 4 - 2 hours)
**Goal**: Prepare framework for future agents

**Steps**:
1. Document framework usage patterns
2. Create agent creation templates
3. Add monitoring/logging utilities
4. Write migration guide for other agents
5. Performance optimization recommendations

**Output**: Reusable framework + documentation

---

## 🎯 **Implementation Strategy**

### **Keep Working (Don't Touch)**
- All existing tools (`@function_tool` pattern)
- Redis orchestrator workflow logic
- Pydantic models 
- Database connections
- Error handling patterns

### **Replace Only**
- `Agent()` constructors → `CustomAgent()`
- `Runner.run()` calls → `CustomRunner.execute_plan()`
- Agent SDK imports → Custom framework imports

### **Migration Pattern**
```python
# OLD (Agent SDK)
agent = Agent(name="X", instructions="Y", tools=[...])
result = await Runner.run(agent, input_text)

# NEW (Custom Framework)  
agent = CustomAgent(name="X", instructions="Y", tools=[...])
result = await CustomRunner.execute_plan(agent, input_text)
```

---

## ✅ **Success Criteria**

### **Performance**
- [ ] Consistent timing (±10% variance max)
- [ ] Sub-10s execution for standard memory requests
- [ ] Parallel execution working (verified logs)

### **Functionality**
- [ ] All existing memory features working
- [ ] Redis state management intact
- [ ] Error handling preserved
- [ ] Database integration unchanged

### **Reusability**
- [ ] Framework works for non-memory agents
- [ ] Simple agent creation pattern
- [ ] Clear documentation
- [ ] Migration templates ready

---

## 🚨 **Risks & Mitigation**

### **Risk 1**: Framework complexity grows
**Mitigation**: Start simple, add features incrementally

### **Risk 2**: Performance doesn't improve  
**Mitigation**: Keep Agent SDK as fallback during testing

### **Risk 3**: Redis logic breaks during migration
**Mitigation**: Keep orchestrator logic identical, just change execution

### **Risk 4**: Tool integration issues
**Mitigation**: Keep `@function_tool` pattern unchanged

---

## 🎉 **Expected Benefits**

### **Immediate** (Post-Migration)
- Consistent 5-10s performance
- No more 42s random delays
- Debuggable execution flow
- Full control over optimization

### **Long-term** (Future Agents)
- Reusable framework for any agent type
- Faster development cycles
- Consistent patterns across all agents
- No vendor lock-in to Agent SDK

### **Development Experience**
- Clear debugging capabilities
- Performance profiling possible
- Customizable execution strategies
- Framework evolution under our control

---

## 📝 **Next Actions**

1. **Start Phase 1**: Create `app/framework/` and extract orchestration logic
2. **Keep current system running**: No downtime during migration
3. **Parallel development**: Build new while old system handles production
4. **Gradual cutover**: Test new system thoroughly before switching
5. **Document everything**: Ensure team can maintain custom framework

**Timeline**: 3-4 days for complete migration + testing
**Risk Level**: Low (keeping existing logic, just changing execution layer)
**ROI**: High (performance + reusability + future-proofing) 