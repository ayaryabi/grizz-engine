# 🔄 **LangGraph Migration Plan - From OpenAI Agent SDK to State Machine Orchestration**

## 📋 **Executive Summary**

This document provides a comprehensive migration plan from OpenAI Agent SDK to LangGraph for the Grizz Engine AI system. The migration will transform our current agent-based architecture into a stateful, graph-based workflow system that offers greater flexibility, control, and debugging capabilities.

---

## 🎯 **Current Architecture Analysis**

### **OpenAI Agent SDK Implementation**
- **Primary Pattern**: Inheritance-based agents using `agents.Agent` class
- **Tool Integration**: `@function_tool` decorators with `Runner.run()` orchestration
- **Memory System**: Complex planner→actor workflow with Agent SDK handoffs
- **Streaming**: Agent SDK's `Runner.run_streamed()` with event processing
- **State Management**: Implicit state through Agent SDK's message management

### **Key Files in Current Architecture**
```
Core Agent Infrastructure:
├── app/agents/base_agent.py          # BaseGrizzAgent inherits from agents.Agent
├── app/agents/chat_agent.py          # ChatAgent with tools integration
├── app/workers/llm_worker.py         # Worker with Agent SDK streaming

Memory System:
├── app/agents/memory/master_memory_agent.py     # Tool wrapper
├── app/agents/memory/memory_manager.py          # Agent handoff orchestration
├── app/agents/memory/actor_agent.py             # Complex execution agent

Tool System:
├── app/tools/search_tools.py         # @function_tool implementations
├── app/tools/categorization_tools.py # Agent SDK based tools
├── app/tools/markdown_tools.py       # Agent SDK based tools
├── app/tools/summarization_tools.py  # Agent SDK based tools
├── app/tools/memory_tools.py         # Simple function tools

Data Models:
├── app/models/agents.py              # Pydantic models for memory plans
├── app/models/memory.py              # Memory data structures
├── app/models/tools.py               # Tool input/output models
```

---

## 🏗️ **LangGraph Architecture Overview**

### **Core Concepts**
1. **StateGraph**: Explicit state management with type-safe reducers
2. **Nodes**: Pure functions that transform state
3. **Edges**: Control flow between nodes (simple, conditional, or parallel)
4. **State**: TypedDict or Pydantic models with explicit update patterns
5. **Tools**: Standard function definitions (no decorators needed)

### **Comparison: Agent SDK vs LangGraph**

| Feature | OpenAI Agent SDK | LangGraph |
|---------|------------------|-----------|
| **Architecture** | Inheritance-based agents | Functional nodes + state |
| **State Management** | Implicit in Agent messages | Explicit StateGraph |
| **Tool Definition** | `@function_tool` decorators | Standard Python functions |
| **Workflow Control** | Agent handoffs with Runner | Graph edges and conditions |
| **Debugging** | Limited visibility | Full graph visualization |
| **Streaming** | Agent SDK event processing | Node-level streaming |
| **Flexibility** | Agent SDK constraints | Full control over execution |
| **Memory** | Agent context management | Explicit state persistence |

---

## 🚀 **Migration Plan**

### **Phase 1: Foundation Setup** (2-3 hours)

#### **1.1 Install LangGraph Dependencies**
```bash
pip install langgraph==0.2.50
pip install langchain-core==0.3.15
```

#### **1.2 Create New State Definitions**
**File: `app/graph/state.py`** (NEW)
```python
from typing import TypedDict, Annotated, List, Optional, Any, Dict
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
import operator

class ChatState(TypedDict):
    """Main chat state for LangGraph workflows"""
    # Message management with built-in reducer
    messages: Annotated[List[AnyMessage], add_messages]
    
    # User context
    user_id: str
    conversation_id: str
    
    # File handling
    file_urls: Annotated[List[str], operator.add]
    
    # Memory workflow state
    memory_operation: Optional[Dict[str, Any]]
    memory_results: Optional[Dict[str, Any]]
    
    # Search results
    search_results: Optional[str]

class MemoryWorkflowState(TypedDict):
    """Specialized state for memory operations"""
    # Core content
    original_message: str
    content_to_save: str
    
    # Processing results
    formatted_content: Optional[str]
    categorization_result: Optional[Dict[str, Any]]
    summary: Optional[str]
    
    # Final output
    memory_id: Optional[str]
    success: bool
    error_message: Optional[str]
```

#### **1.3 Create Core Graph Utilities**
**File: `app/graph/utils.py`** (NEW)
```python
from typing import Any, Dict
from langchain_core.messages import HumanMessage, AIMessage
from .state import ChatState

def should_use_tools(state: ChatState) -> str:
    """Conditional edge function to determine tool usage"""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "respond"

def format_tool_results(results: List[Any]) -> str:
    """Format tool execution results for display"""
    if not results:
        return "No results"
    
    formatted = []
    for result in results:
        if isinstance(result, dict):
            formatted.append(str(result))
        else:
            formatted.append(str(result))
    
    return "\n".join(formatted)

def create_error_message(error: str) -> AIMessage:
    """Create standardized error message"""
    return AIMessage(content=f"❌ Error: {error}")
```

### **Phase 2: Tool Migration** (1-2 hours)

#### **2.1 Convert Function Tools to Standard Functions**
**File: `app/graph/tools.py`** (NEW)
```python
from typing import List, Dict, Any
from langchain_core.tools import tool
from ..tools.search_tools import _perplexity_search_core
from ..tools.memory_tools import save_memory_tool
from ..models.tools import *

# Standard LangChain tool definitions (no Agent SDK decorators)
@tool
async def web_search_tool(query: str, search_mode: str = "fast") -> str:
    """Search the web using Perplexity API"""
    return await _perplexity_search_core(query, search_mode)

@tool 
async def memory_save_tool(
    content: str, 
    title: str = "", 
    category: str = "general"
) -> Dict[str, Any]:
    """Save content to memory"""
    from ..models.memory import SaveMemoryInput
    
    input_data = SaveMemoryInput(
        item_type="note",
        title=title or content[:50] + "...",
        content=content,
        properties={},
        category=category
    )
    
    result = await save_memory_tool(input_data)
    return {
        "success": result.success,
        "memory_id": result.id,
        "title": result.title,
        "message": result.message
    }

# Tool registry for LangGraph
AVAILABLE_TOOLS = [
    web_search_tool,
    memory_save_tool,
]
```

#### **2.2 Update Base Tool Implementations**
**Modify: `app/tools/search_tools.py`**
Remove `@function_tool` decorator, keep core functionality:
```python
# Remove: from agents import function_tool
# Remove: @function_tool decorator

# Keep the core function as-is
async def _perplexity_search_core(query: str, search_mode: str = "fast") -> str:
    # Existing implementation stays the same
    pass
```

**Similar updates needed for:**
- `app/tools/categorization_tools.py`
- `app/tools/markdown_tools.py` 
- `app/tools/summarization_tools.py`

### **Phase 3: Core Graph Implementation** (2-3 hours)

#### **3.1 Create Main Chat Graph**
**File: `app/graph/chat_graph.py`** (NEW)
```python
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from .state import ChatState
from .tools import AVAILABLE_TOOLS
from .utils import should_use_tools

# Initialize LLM with tools
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    max_tokens=4000
).bind_tools(AVAILABLE_TOOLS)

async def chat_agent_node(state: ChatState) -> Dict[str, Any]:
    """Main chat agent node - equivalent to current ChatAgent"""
    
    # Build Grizz personality prompt
    system_prompt = """You are **Grizz**, a bear-like AI companion designed for Gen Z users...
    [Full personality from current chat_agent.py]
    """
    
    # Prepare messages with system prompt
    messages = [HumanMessage(content=system_prompt)] + state["messages"]
    
    # Invoke LLM
    response = await llm.ainvoke(messages)
    
    return {"messages": [response]}

async def tool_execution_node(state: ChatState) -> Dict[str, Any]:
    """Execute tools based on last message tool calls"""
    from langgraph.prebuilt import ToolNode
    
    tool_node = ToolNode(AVAILABLE_TOOLS)
    result = await tool_node.ainvoke(state)
    
    return result

def create_chat_graph() -> StateGraph:
    """Create the main chat workflow graph"""
    
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("agent", chat_agent_node)
    workflow.add_node("tools", tool_execution_node)
    
    # Define flow
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_use_tools,
        {
            "tools": "tools",
            "respond": END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
```

#### **3.2 Create Memory Workflow Graph**
**File: `app/graph/memory_graph.py`** (NEW)
```python
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from .state import MemoryWorkflowState
from ..tools.markdown_tools import markdown_formatter
from ..tools.categorization_tools import categorization_agent
from ..tools.memory_tools import save_memory_tool

async def format_content_node(state: MemoryWorkflowState) -> Dict[str, Any]:
    """Format content into clean markdown"""
    try:
        formatted = await markdown_formatter.format({
            "content": state["content_to_save"],
            "item_type": "note"
        })
        return {"formatted_content": formatted.formatted_content}
    except Exception as e:
        return {"error_message": f"Formatting failed: {str(e)}"}

async def categorize_content_node(state: MemoryWorkflowState) -> Dict[str, Any]:
    """Categorize content and extract properties"""
    try:
        content = state.get("formatted_content") or state["content_to_save"]
        
        result = await categorization_agent.categorize({
            "content": content,
            "item_type": "note",
            "conversation_context": state["original_message"],
            "user_intent": ""
        })
        
        return {
            "categorization_result": {
                "category": result.category,
                "properties": result.properties,
                "confidence": result.confidence
            }
        }
    except Exception as e:
        return {"error_message": f"Categorization failed: {str(e)}"}

async def save_memory_node(state: MemoryWorkflowState) -> Dict[str, Any]:
    """Save processed content to memory"""
    try:
        content = state.get("formatted_content") or state["content_to_save"]
        category = state.get("categorization_result", {}).get("category", "general")
        
        result = await save_memory_tool({
            "item_type": "note",
            "title": content[:50] + "..." if len(content) > 50 else content,
            "content": content,
            "properties": state.get("categorization_result", {}).get("properties", {}),
            "category": category
        })
        
        return {
            "memory_id": result.id,
            "success": True
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Save failed: {str(e)}"
        }

def create_memory_workflow() -> StateGraph:
    """Create memory processing workflow"""
    
    workflow = StateGraph(MemoryWorkflowState)
    
    # Add nodes in dependency order
    workflow.add_node("format", format_content_node)
    workflow.add_node("categorize", categorize_content_node)  
    workflow.add_node("save", save_memory_node)
    
    # Linear workflow with error handling
    workflow.set_entry_point("format")
    workflow.add_edge("format", "categorize")
    workflow.add_edge("categorize", "save")
    workflow.add_edge("save", END)
    
    return workflow.compile()
```

### **Phase 4: Worker Integration** (1-2 hours)

#### **4.1 Create LangGraph Worker Adapter**
**File: `app/graph/worker_adapter.py`** (NEW)
```python
from typing import Dict, Any, AsyncIterator
import asyncio
from .chat_graph import create_chat_graph
from .state import ChatState
from langchain_core.messages import HumanMessage

class LangGraphWorkerAdapter:
    """Adapter to integrate LangGraph with existing worker system"""
    
    def __init__(self):
        self.chat_graph = create_chat_graph()
    
    async def process_message(
        self, 
        message: str,
        conversation_history: list,
        user_id: str,
        conversation_id: str,
        file_urls: list = None
    ) -> AsyncIterator[str]:
        """Process message through LangGraph and yield chunks"""
        
        # Convert to LangGraph state
        initial_state = ChatState(
            messages=conversation_history + [HumanMessage(content=message)],
            user_id=user_id,
            conversation_id=conversation_id,
            file_urls=file_urls or [],
            memory_operation=None,
            memory_results=None,
            search_results=None
        )
        
        # Stream through graph
        async for chunk in self.chat_graph.astream(initial_state):
            # Extract message content from chunk
            if "messages" in chunk:
                last_message = chunk["messages"][-1]
                if hasattr(last_message, 'content'):
                    yield last_message.content
                    
    async def get_final_response(
        self,
        message: str,
        conversation_history: list,
        user_id: str,
        conversation_id: str,
        file_urls: list = None
    ) -> str:
        """Get complete response (non-streaming)"""
        
        chunks = []
        async for chunk in self.process_message(
            message, conversation_history, user_id, conversation_id, file_urls
        ):
            chunks.append(chunk)
        
        return "".join(chunks)
```

#### **4.2 Modify Worker to Use LangGraph**
**Modify: `app/workers/llm_worker.py`**
```python
# Add import
from app.graph.worker_adapter import LangGraphWorkerAdapter

# Replace Agent SDK imports with LangGraph adapter
# Remove: from agents import Runner, RunContextWrapper
# Remove: from app.agents.chat_agent import chat_agent

# Initialize LangGraph adapter
langgraph_adapter = LangGraphWorkerAdapter()

async def process_chat_job(redis_conn: redis.Redis, job_data: Dict[str, Any]) -> bool:
    """Modified to use LangGraph instead of Agent SDK"""
    
    # ... existing setup code ...
    
    # Replace Agent SDK streaming with LangGraph streaming
    try:
        async for chunk in langgraph_adapter.process_message(
            message=message,
            conversation_history=context,
            user_id=user_id,
            conversation_id=conversation_id,
            file_urls=file_urls
        ):
            await publish_result_chunk(
                redis_conn,
                job_id,
                chunk,
                client_id,
                is_final=False
            )
            full_response += chunk
        
        # Send final chunk
        await publish_result_chunk(
            redis_conn,
            job_id,
            "",
            client_id,
            is_final=True
        )
        
        # ... existing save logic ...
        
    except Exception as e:
        # ... existing error handling ...
```

### **Phase 5: Memory System Migration** (2-3 hours)

#### **5.1 Create Memory Graph Integration**
**File: `app/graph/memory_integration.py`** (NEW)
```python
from langchain_core.tools import tool
from .memory_graph import create_memory_workflow
from .state import MemoryWorkflowState

memory_workflow = create_memory_workflow()

@tool
async def process_memory_request(content: str, user_message: str) -> str:
    """Process memory save request through LangGraph workflow"""
    
    initial_state = MemoryWorkflowState(
        original_message=user_message,
        content_to_save=content,
        formatted_content=None,
        categorization_result=None,
        summary=None,
        memory_id=None,
        success=False,
        error_message=None
    )
    
    # Execute memory workflow
    result = await memory_workflow.ainvoke(initial_state)
    
    if result["success"]:
        return f"✅ Memory saved successfully! ID: {result['memory_id']}"
    else:
        return f"❌ Memory save failed: {result.get('error_message', 'Unknown error')}"
```

#### **5.2 Update Memory Tool Registration**
**Modify: `app/graph/tools.py`**
```python
# Add memory integration
from .memory_integration import process_memory_request

# Update tool registry
AVAILABLE_TOOLS = [
    web_search_tool,
    process_memory_request,  # Replace memory_save_tool
]
```

### **Phase 6: Testing & Validation** (1-2 hours)

#### **6.1 Create Test Suite**
**File: `tests/test_langgraph_migration.py`** (NEW)
```python
import pytest
import asyncio
from app.graph.chat_graph import create_chat_graph
from app.graph.state import ChatState
from langchain_core.messages import HumanMessage

class TestLangGraphMigration:
    
    @pytest.fixture
    def chat_graph(self):
        return create_chat_graph()
    
    async def test_basic_chat(self, chat_graph):
        """Test basic chat functionality"""
        state = ChatState(
            messages=[HumanMessage(content="Hello, what's 2+2?")],
            user_id="test_user",
            conversation_id="test_conv",
            file_urls=[],
            memory_operation=None,
            memory_results=None,
            search_results=None
        )
        
        result = await chat_graph.ainvoke(state)
        assert "messages" in result
        assert len(result["messages"]) > 1
    
    async def test_tool_usage(self, chat_graph):
        """Test tool integration"""
        state = ChatState(
            messages=[HumanMessage(content="Search for latest AI news")],
            user_id="test_user", 
            conversation_id="test_conv",
            file_urls=[],
            memory_operation=None,
            memory_results=None,
            search_results=None
        )
        
        result = await chat_graph.ainvoke(state)
        # Verify tool was called and results integrated
        assert result is not None
```

#### **6.2 Create Migration Verification Script**
**File: `scripts/verify_migration.py`** (NEW)
```python
"""Verification script to ensure LangGraph migration maintains functionality"""

import asyncio
from app.graph.worker_adapter import LangGraphWorkerAdapter

async def test_migration():
    adapter = LangGraphWorkerAdapter()
    
    # Test basic chat
    response = await adapter.get_final_response(
        message="Hello Grizz!",
        conversation_history=[],
        user_id="test_user",
        conversation_id="test_conv"
    )
    print(f"Basic chat test: {response[:100]}...")
    
    # Test search functionality
    response = await adapter.get_final_response(
        message="Search for Python tutorials",
        conversation_history=[],
        user_id="test_user", 
        conversation_id="test_conv"
    )
    print(f"Search test: {response[:100]}...")
    
    # Test memory functionality
    response = await adapter.get_final_response(
        message="Remember that I love Python programming",
        conversation_history=[],
        user_id="test_user",
        conversation_id="test_conv"
    )
    print(f"Memory test: {response[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_migration())
```

---

## 📁 **File-by-File Migration Order**

### **High Priority - Core Infrastructure**
1. **`app/graph/state.py`** - NEW: State definitions
2. **`app/graph/utils.py`** - NEW: Graph utilities
3. **`app/graph/tools.py`** - NEW: Tool registry
4. **`app/graph/chat_graph.py`** - NEW: Main chat graph
5. **`app/workers/llm_worker.py`** - MODIFY: Replace Agent SDK

### **Medium Priority - Memory System**
6. **`app/graph/memory_graph.py`** - NEW: Memory workflow
7. **`app/graph/memory_integration.py`** - NEW: Memory tool integration
8. **`app/graph/worker_adapter.py`** - NEW: Worker adapter

### **Low Priority - Tool Updates**
9. **`app/tools/search_tools.py`** - MODIFY: Remove Agent SDK decorators
10. **`app/tools/categorization_tools.py`** - MODIFY: Remove Agent SDK
11. **`app/tools/markdown_tools.py`** - MODIFY: Remove Agent SDK
12. **`app/tools/summarization_tools.py`** - MODIFY: Remove Agent SDK

### **Optional - Legacy Cleanup**
13. **`app/agents/base_agent.py`** - DEPRECATED: Can be removed after migration
14. **`app/agents/chat_agent.py`** - DEPRECATED: Can be removed after migration
15. **`app/agents/memory/`** - DEPRECATED: Can be removed after migration

---

## 🎯 **Key Benefits of Migration**

### **1. Enhanced Debugging & Visualization**
- **Current**: Black box Agent SDK execution
- **LangGraph**: Full graph visualization and step-by-step debugging

### **2. Explicit State Management**
- **Current**: Implicit state in Agent SDK messages
- **LangGraph**: Type-safe state with explicit reducers

### **3. Better Error Handling**
- **Current**: Agent SDK error handling limitations
- **LangGraph**: Per-node error handling and retry policies

### **4. Improved Flexibility**
- **Current**: Agent SDK workflow constraints
- **LangGraph**: Full control over execution flow and parallelism

### **5. Production Readiness**
- **Current**: Agent SDK stability issues
- **LangGraph**: Mature, production-tested framework

---

## ⚠️ **Migration Risks & Mitigation**

### **Risk 1: Behavioral Changes**
- **Risk**: LangGraph responses may differ from Agent SDK
- **Mitigation**: Extensive A/B testing with current prompts

### **Risk 2: Performance Impact**
- **Risk**: Different execution patterns may affect latency
- **Mitigation**: Performance benchmarking before/after

### **Risk 3: Tool Compatibility**
- **Risk**: Tool integration patterns may break
- **Mitigation**: Gradual tool migration with fallbacks

### **Risk 4: Memory System Complexity**
- **Risk**: Memory workflow may be harder to debug
- **Mitigation**: Comprehensive logging and graph visualization

---

## 🚀 **Deployment Strategy**

### **Phase A: Parallel Development**
1. Develop LangGraph implementation alongside Agent SDK
2. Use feature flags to toggle between systems
3. Validate functionality parity

### **Phase B: Gradual Rollout**
1. Deploy to 10% of traffic
2. Monitor for issues and performance impact
3. Gradually increase to 100%

### **Phase C: Legacy Cleanup**
1. Remove Agent SDK dependencies
2. Clean up deprecated files
3. Update documentation

---

## 📊 **Expected Timeline**

| Phase | Duration | Effort | Priority |
|-------|----------|--------|----------|
| Foundation Setup | 2-3 hours | High | Critical |
| Tool Migration | 1-2 hours | Medium | High |
| Core Graph Implementation | 2-3 hours | High | Critical |  
| Worker Integration | 1-2 hours | High | Critical |
| Memory System Migration | 2-3 hours | Medium | High |
| Testing & Validation | 1-2 hours | Medium | High |

**Total Estimated Time: 9-15 hours**

---

## 🎉 **Conclusion**

This migration from OpenAI Agent SDK to LangGraph represents a significant architectural improvement that will provide:

- **Better reliability** - No more tool disappearing issues
- **Enhanced debugging** - Full graph visualization and tracing
- **Greater flexibility** - Custom workflows and parallel execution
- **Production readiness** - Mature framework with proven scalability

The modular architecture of your current system makes this migration highly feasible, with most changes being additive rather than destructive. The investment in this migration will pay dividends in terms of system stability, debuggability, and future extensibility. 