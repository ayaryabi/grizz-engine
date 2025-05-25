# AI Migration Roadmap: LLM → Agents SDK → Memory System

## Overview
Migrate Grizz Engine from direct OpenAI calls to OpenAI Agents SDK, then implement the **Memory System** with planner-actor agents for saving and organizing user information.

**Timeline:** ~5-7 hours total (incremental, testable phases)

---

## What We're Building

**Goal:** Transform current simple chat into intelligent memory-aware system with multimodal support:

0. **Phase 0:** Multimodal LLM Manager Foundation (30 min)
1. **Phase 1:** Basic Agent SDK migration (30-60 min)
2. **Phase 2:** Agent architecture + Pydantic models (45 min)  
3. **Phase 3:** Simple Memory Agent (45 min)
4. **Phase 4:** Planner-Actor system (1.5 hours)
5. **Phase 5:** Core memory tools (2 hours)

**Final Result:**
```
User Query → Main Chat Agent → (decides to use memory_manager_tool) → Memory Planner → Memory Actor → [Save, Tag, etc.] → Back to Chat Agent → Response

OR

User Query → Main Chat Agent → (responds directly) → Response
```

---

## Target Architecture

### Folder Structure
```
ai-engine/
├── app/
│   ├── models/                    # 🎯 Pydantic models (NEW)
│   │   ├── __init__.py
│   │   ├── memory.py             # Memory business models
│   │   ├── tools.py              # Tool input/output schemas
│   │   └── agents.py             # Agent coordination models
│   ├── agents/                    # Agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py         # 🎯 Common agent functionality
│   │   ├── main_chat_agent.py    # 🎯 MAIN agent with memory + vision tools
│   │   ├── vision_agent.py       # 🎯 Multimodal vision specialist (NEW)
│   │   └── memory/               # Memory System (internal)
│   │       ├── __init__.py
│   │       ├── planner_agent.py  # Plans memory tasks
│   │       ├── actor_agent.py    # Executes plans
│   │       └── memory_manager.py # Coordinator (exposed as tool)
│   ├── tools/                    # Shared tool ecosystem
│   │   ├── __init__.py
│   │   ├── memory_tools.py       # Save to Postgres
│   │   ├── vision_tools.py       # 🎯 Image analysis tools (NEW)
│   │   ├── tagging_tools.py      # Auto-categorization
│   │   └── markdown_tools.py     # MD conversion
│   ├── llm/                      # Enhanced LLM management
│   │   ├── __init__.py
│   │   ├── openai_client.py      # Current implementation (backward compatible)
│   │   └── llm_manager.py        # 🎯 Multi-LLM manager (NEW)
│   └── workers/                  # Current workers
```

### Example Memory Flow
```
1. User: "Save this lecture transcript about AI for my computer science notes"
2. Main Chat Agent: Analyzes message → decides to use memory_manager_tool
3. Memory Manager Tool: Internally creates Memory Planner
4. Memory Planner: Creates MemoryPlan object:
   - Convert transcript to markdown
   - Categorize as "computer_science" 
   - Tag with "AI", "lecture", "notes"
   - Save to database
5. Memory Actor: Executes each PlanStep using tools
6. Memory Manager Tool: Returns result to Main Chat Agent
7. Main Chat Agent: "Saved AI lecture to computer science category with 3 tags"
```

---

## Phase 0: Multimodal LLM Manager Foundation
**Time:** 30 minutes

**Goal:** Create SDK-compatible multi-LLM architecture with multimodal support from day 1, inspired by Co-Sight's proven pattern.

### What We're Building
1. **Install OpenAI Agents SDK**: `pip install openai-agents`
2. **Multi-LLM Manager** (`app/llm/llm_manager.py`): 
   - Specialized configs: chat, planning, execution, vision
   - Uses `gpt-4o` for multimodal, `gpt-4o-mini` for fast execution
   - Backward compatible with existing `stream_chat_completion()`
3. **Base Agent Infrastructure** (`app/agents/base_agent.py`):
   - `BaseGrizzAgent` class with SDK integration
   - `process_multimodal()` method for text + images
   - Different LLM types for different agent purposes

### Benefits Achieved
- **🎯 Multimodal Foundation**: Ready for images/vision from day 1
- **🚀 Performance Options**: Different models for different tasks
- **🔄 Backward Compatible**: Existing code continues working
- **📊 Co-Sight Proven Pattern**: Based on production-tested architecture

### Test
- Verify new files load without errors
- Confirm existing `stream_chat_completion()` still works
- Test multimodal capability with image URL

---

## Phase 1: Basic Agent SDK Migration
**Time:** 30-60 minutes

**Goal:** Start using the Agent SDK with the new multi-LLM manager while maintaining identical chat experience.

### What Changes
- **File:** `ai-engine/app/workers/llm_worker.py` 
- **Action:** Update to use new `llm_manager.stream_chat()` instead of direct `stream_chat_completion()`
- **File:** `ai-engine/app/agents/chat_agent.py` (if exists)
- **Action:** Migrate to use `BaseGrizzAgent` pattern

### What Stays Same
- WebSocket layer - zero changes
- Redis queues - zero changes  
- Database - zero changes
- Current chat experience - identical

### Test
Send normal chat message, verify same streaming response

---

## Phase 2: Agent Architecture + Pydantic Models
**Time:** 45 minutes

> **🎯 Why Pydantic?** Based on [Pydantic's LLM steering capabilities](https://pydantic.dev/articles/llm-intro), Pydantic forces LLMs to return **exact structured output** instead of vague text. This is crucial for our planner-actor system where we need precise, executable plans.

### Create Pydantic Models Structure
```python
# app/models/memory.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

class MemoryCreate(BaseModel):
    """For creating new memories"""
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50000)
    category: str = Field(description="Category for organization")
    tags: List[str] = Field(default_factory=list)

class MemoryInDB(BaseModel):
    """Memory as stored in database"""
    id: str
    user_id: str
    title: str
    content: str
    category: str
    tags: List[str]
    created_at: datetime

class MemoryResponse(BaseModel):
    """Memory returned to user"""
    id: str
    title: str
    category: str
    tags: List[str]
    created_at: datetime

# app/models/agents.py
class PlanStep(BaseModel):
    """Forces planner to return exact step structure"""
    step_id: str = Field(description="Unique step identifier")
    action: Literal["categorize", "save", "format", "tag"] = Field(
        description="Exact action type - must be one of these"
    )
    tool_name: str = Field(description="Exact tool function name")
    parameters: Dict[str, Any] = Field(description="Tool parameters")
    dependencies: List[str] = Field(default_factory=list)
    description: str = Field(description="Human readable step description")

class MemoryPlan(BaseModel):
    """Forces planner agent to return structured plan"""
    plan_id: str
    user_request: str = Field(description="Original user request")
    steps: List[PlanStep] = Field(description="Ordered execution steps")
    estimated_time: int = Field(description="Estimated time in seconds")

# app/models/tools.py
class SaveMemoryInput(BaseModel):
    """Forces save tool to get exact inputs"""
    content: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    category: str
    user_id: str
    tags: List[str] = Field(default_factory=list)

class SaveMemoryOutput(BaseModel):
    """Forces save tool to return exact outputs"""
    success: bool
    memory_id: str
    message: str
    category_used: str
    tags_assigned: List[str]
```

### Create Base Agent Infrastructure
```python
# app/agents/base_agent.py
from agents import Agent, Runner
from typing import List, Dict, Any, Optional

class BaseGrizzAgent:
    """Common functionality for all Grizz agents"""
    
    def __init__(self, name: str, instructions: str, tools: List = None, output_type = None):
        self.agent = Agent(
            name=name,
            model="gpt-4o", 
            instructions=instructions,
            tools=tools or [],
            output_type=output_type  # 🎯 This forces structured output
        )
    
    async def process(self, user_input: str):
        result = await Runner.run(self.agent, user_input)
        return result.final_output

# app/agents/chat_agent.py  
class ChatAgent(BaseGrizzAgent):
    """Basic conversational agent (current functionality)"""
    
    def __init__(self):
        super().__init__(
            name="Chat Agent",
            instructions="You are a helpful conversational assistant.",
            tools=[]  # No tools, just conversation
        )
```

### Import Structure
```python
# app/models/__init__.py
from .memory import MemoryCreate, MemoryInDB, MemoryResponse
from .agents import PlanStep, MemoryPlan
from .tools import SaveMemoryInput, SaveMemoryOutput

__all__ = [
    "MemoryCreate", "MemoryInDB", "MemoryResponse",
    "PlanStep", "MemoryPlan",
    "SaveMemoryInput", "SaveMemoryOutput"
]
```

### Test
- Verify models load without errors
- Can create `MemoryCreate(title="test", content="test", category="test")`
- Chat still works via ChatAgent

---

## Phase 3: Simple Memory Agent
**Time:** 45 minutes

### Implement Memory Manager as Tool
```python
# app/agents/memory/memory_manager.py
from ..base_agent import BaseGrizzAgent
from ...models.tools import SaveMemoryInput, SaveMemoryOutput
from agents import function_tool

class MemoryManager:
    """Memory management system exposed as tool to main chat agent"""
    
    def __init__(self):
        self.memory_agent = BaseGrizzAgent(
            name="Memory Manager",
            instructions="""
            You help users save and organize their information.
            When users want to save content, use the save_memory tool.
            Always provide clear confirmation of what was saved.
            """,
            tools=[save_memory_placeholder]  # Will implement in Phase 5
        )
    
    async def process_memory_request(self, user_request: str) -> str:
        """Process memory-related requests"""
        result = await self.memory_agent.process(user_request)
        return result

# Create memory manager tool for main chat agent
memory_manager = MemoryManager()

@function_tool
async def memory_manager_tool(action: str, content: str = "") -> str:
    """
    Manage user memories and information storage.
    
    Use this tool when users want to save, store, remember, or organize information.
    
    Args:
        action: What to do - save, search, organize, etc.
        content: The content to work with
    """
    request = f"Action: {action}\nContent: {content}"
    result = await memory_manager.process_memory_request(request)
    return result

# app/agents/main_chat_agent.py
from .base_agent import BaseGrizzAgent
from .memory.memory_manager import memory_manager_tool

class MainChatAgent(BaseGrizzAgent):
    """Main conversational agent with memory capabilities"""
    
    def __init__(self):
        super().__init__(
            name="Grizz Assistant",
            instructions="""
            You are Grizz, a helpful AI assistant with memory capabilities.
            
            You have access to a memory management system. Use the memory_manager_tool when users:
            - Want to save or store information
            - Ask you to remember something
            - Want to organize their notes or data
            - Use words like "save", "store", "remember", "note this down"
            
            For regular conversations, respond normally without using tools.
            """,
            tools=[memory_manager_tool]  # Main agent has memory tool available
        )

# app/workers/llm_worker.py - Updated to use single main agent
from app.agents.main_chat_agent import MainChatAgent

main_chat_agent = MainChatAgent()

async def process_message(user_message: str, user_id: str):
    """Process all messages through main chat agent"""
    return await main_chat_agent.process(user_message)
```

### Test
- "Save this as a note" → Main agent uses memory_manager_tool
- "How's the weather?" → Main agent responds directly (no tools)
- Verify single agent handles both scenarios intelligently

---

## Phase 4: Planner-Actor System  
**Time:** 1.5 hours

### Redis State Management for Plans

**Key Insight:** We extend existing Redis infrastructure with **hashes** for plan state management:

- **Current Redis streams:** Continue handling job queues and result delivery (unchanged)
- **New Redis hashes:** Store plan state while execution happens
- **Plan state keys:** `plan:{conversation_id}:{plan_id}` 
- **Hash fields:** plan_json, status, current_step, step_results, created_at
- **State updates:** As each step completes, update hash with results
- **Automatic cleanup:** Set TTL (1 hour) to prevent memory growth
- **Zero new infrastructure:** Uses existing `get_redis_pool()` and `safe_redis_operation()`

**Benefits:**
- Plan progress survives worker restarts
- Real-time status tracking for UI
- Easy debugging of stuck plans
- Scalable alongside existing Redis setup

### Split Memory Agent Into Two
```python
# app/agents/memory/planner_agent.py
from ..base_agent import BaseGrizzAgent
from ...models.agents import MemoryPlan
from agents import handoff

class MemoryPlannerAgent(BaseGrizzAgent):
    """Creates structured plans for memory operations"""
    
    def __init__(self, actor_agent):
        super().__init__(
            name="Memory Planner",
            instructions="""
            You create detailed execution plans for memory operations.
            
            IMPORTANT: Return a valid MemoryPlan with:
            - step_id: unique identifier
            - action: must be "categorize", "save", "format", or "tag"
            - tool_name: exact function name to call
            - parameters: exact parameters for the tool
            - dependencies: list of step_ids that must complete first
            
            Always hand off the plan to the actor for execution.
            """,
            output_type=MemoryPlan,  # 🎯 Forces structured plan output
            handoffs=[self._transfer_to_actor]
        )
        self.actor_agent = actor_agent
    
    @handoff
    def _transfer_to_actor(self):
        """Transfer structured plan to actor for execution"""
        return self.actor_agent

# app/agents/memory/actor_agent.py  
from ..base_agent import BaseGrizzAgent
from ...models.agents import MemoryPlan, PlanStep

class MemoryActorAgent(BaseGrizzAgent):
    """Executes structured plans step by step"""
    
    def __init__(self):
        super().__init__(
            name="Memory Actor",
            instructions="""
            Execute MemoryPlan objects step by step:
            
            1. Process steps in dependency order
            2. Call exact tool_name with exact parameters
            3. Report progress and results
            4. Handle any step failures gracefully
            """,
            tools=[]  # Will add tools in Phase 5
        )
    
    async def execute_plan(self, plan: MemoryPlan) -> str:
        """Execute structured plan using Pydantic guarantees"""
        results = []
        
        for step in plan.steps:
            # Pydantic guarantees these fields exist and have correct types
            tool_name = step.tool_name  # guaranteed string
            parameters = step.parameters  # guaranteed dict
            
            result = await self.call_tool(tool_name, **parameters)
            results.append(f"✅ {step.description}: {result}")
        
        return "\n".join(results)
```

### Test
- "Save this Python tutorial for my programming notes"
- Verify: Planner creates MemoryPlan → Actor receives structured plan
- Check logs for two-agent conversation with exact data structures

---

## Phase 5: Core Memory Tools
**Time:** 2 hours

### Implement Real Tools with Pydantic
```python
# app/tools/memory_tools.py
from agents import function_tool
from ..models.tools import SaveMemoryInput, SaveMemoryOutput
from ..models.memory import MemoryCreate, MemoryInDB

@function_tool
async def save_to_memory_db(input_data: SaveMemoryInput) -> SaveMemoryOutput:
    """Save to Postgres memory table with validation"""
    
    # Create validated memory object
    memory = MemoryCreate(
        title=input_data.title,
        content=input_data.content,
        category=input_data.category,
        tags=input_data.tags
    )
    
    # Save to database (use existing DB connection)
    memory_record = await db.save_memory(memory, input_data.user_id)
    
    # Return structured output
    return SaveMemoryOutput(
        success=True,
        memory_id=memory_record.id,
        message=f"Saved '{memory.title}' to {memory.category}",
        category_used=memory.category,
        tags_assigned=memory.tags
    )

# app/tools/tagging_tools.py
@function_tool
async def auto_categorize_content(
    content: str,
    existing_categories: List[str],
    user_id: str
) -> Dict[str, Any]:
    """Auto-categorize based on content and user's existing categories"""
    
    # Simple categorization logic (can be enhanced later)
    if any(tech_word in content.lower() for tech_word in 
           ['python', 'javascript', 'code', 'programming']):
        category = "programming"
    elif any(ai_word in content.lower() for ai_word in 
             ['ai', 'machine learning', 'neural network']):
        category = "artificial_intelligence"
    else:
        category = "general"
    
    return {
        "suggested_category": category,
        "confidence": 0.8,
        "suggested_tags": extract_tags_from_content(content)
    }

# Update Actor Agent with real tools
class MemoryActorAgent(BaseGrizzAgent):
    def __init__(self):
        super().__init__(
            name="Memory Actor",
            instructions="Execute memory plans using available tools.",
            tools=[
                save_to_memory_db,
                auto_categorize_content,
                format_as_markdown
            ]
        )
```

### Test Full Workflow
- "I want to save this article about React hooks for my web development studies"
- Verify: Planning → Categorization → Markdown conversion → Database save
- Check database for new memory entry with proper structure
- Confirm Pydantic validation catches any malformed data

---

## Current vs Final Architecture

### Before (Current)
```
User Message → OpenAI Direct → Stream Response
```

### After (Target)  
```
User Message → Main Chat Agent → (uses memory_manager_tool if needed) → Memory Planner → Memory Actor → [Tools] → Stream Response

OR

User Message → Main Chat Agent → (responds directly) → Stream Response
```

**Key Benefits:**
- Same chat experience for normal conversation
- **Structured LLM output** via Pydantic (no parsing needed)
- Intelligent memory system activated when needed via tool use
- **Guaranteed data validation** for all agent communications
- Single agent with extensible tool ecosystem
- Agent-as-Tool pattern for easy extensibility

---

## Testing Strategy

### Phase-by-Phase Verification
```bash
# Phase 1: Basic agent functionality
"Hello, how are you?" → Same response as before

# Phase 2: Pydantic models + basic agents
from app.models.memory import MemoryCreate
memory = MemoryCreate(title="Test", content="Test content", category="test")

# Phase 3: Memory detection
"Save this as a note" → MemoryAgent response  
"What's 2+2?" → ChatAgent response

# Phase 5: Full memory workflow with structured output
"Save this Python cheatsheet for my coding references"
→ Planner creates MemoryPlan object (structured)
→ Actor executes PlanStep objects (structured)  
→ Tools receive/return validated Pydantic objects
→ Database entry created
→ User gets confirmation with details
```

### Success Criteria
- [ ] Normal chat unchanged (Phase 1)
- [ ] Pydantic models load and validate (Phase 2)
- [ ] Agent routing works (Phase 3) 
- [ ] Planner returns structured MemoryPlan (Phase 4)
- [ ] Actor executes structured PlanSteps (Phase 4)
- [ ] Memory saved to database with validation (Phase 5)
- [ ] All LLM outputs are structured (no text parsing needed)

---

## System Extensibility Notes

### Adding New Agents (Future)
**It's as simple as:**

1. **Create Tool-as-Agent:**
```python
@function_tool
async def research_agent_tool(query: str) -> str:
    """Deep research on any topic"""
    research_agent = ResearchAgent()
    return await research_agent.process(query)

# Add to MainChatAgent's tools list
```

2. **Update Main Chat Agent:**
```python
# In main_chat_agent.py
class MainChatAgent(BaseGrizzAgent):
    def __init__(self):
        super().__init__(
            name="Grizz Assistant",
            instructions="""
            You are Grizz with multiple capabilities:
            - Use memory_manager_tool for saving/organizing information
            - Use research_agent_tool for deep research tasks
            - Respond directly for normal conversation
            """,
            tools=[memory_manager_tool, research_agent_tool]  # Just add to tools
        )
```

3. **That's it!** The main agent intelligently decides when to use each tool.

### Examples of Easy Extensions:
- **Code Agent:** `code_agent_tool()` for programming tasks
- **Image Agent:** `image_agent_tool()` for visual processing  
- **File Agent:** `file_agent_tool()` for document operations

### Why This Architecture Scales:
- **Single Smart Agent:** One conversational agent with many tool capabilities
- **Agent-as-Tool:** Complex functionality becomes available as tools
- **Smart Tool Selection:** Main agent decides which tool to use based on context
- **Zero Configuration:** No routing logic needed - just add tools
- **🎯 Structured Communication:** All tool interactions validated by Pydantic

*The beauty: The main chat agent intelligently orchestrates all capabilities. Adding new AI functionality requires just creating a new tool function and adding it to the main agent's tool list. The agent automatically learns when and how to use each tool based on user requests, with **guaranteed data validation** throughout.* 