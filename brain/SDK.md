# OpenAI Agents SDK: The Complete Guide

## Table of Contents

1. [Overview & Core Concepts](#overview--core-concepts)
2. [Installation & Setup](#installation--setup)
3. [Core Components](#core-components)
4. [Model Providers & Support](#model-providers--support)
5. [Agent Patterns & Architectures](#agent-patterns--architectures)
6. [Tools & Function Calling](#tools--function-calling)
7. [Handoffs & Multi-Agent Systems](#handoffs--multi-agent-systems)
8. [Guardrails & Safety](#guardrails--safety)
9. [Tracing & Debugging](#tracing--debugging)
10. [Advanced Examples](#advanced-examples)
11. [Best Practices & Recommendations](#best-practices--recommendations)
12. [Troubleshooting & Common Issues](#troubleshooting--common-issues)
13. [Production Deployment](#production-deployment)

---

## Overview & Core Concepts

### What is OpenAI Agents SDK?

The OpenAI Agents SDK is a **lightweight yet powerful framework** for building multi-agent workflows. It's designed to be:

- **Provider-agnostic**: Works with OpenAI, Anthropic, Google, Mistral, and 100+ other LLMs
- **Multi-agent ready**: Built-in support for agent handoffs and coordination
- **Production focused**: Includes tracing, guardrails, and safety features
- **Flexible**: Supports various agent patterns from simple to complex

### Core Concepts

#### 1. **Agents**
LLMs configured with instructions, tools, guardrails, and handoffs
```python
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    tools=[get_weather],
    handoffs=[other_agent]
)
```

#### 2. **Handoffs**
Specialized tool calls for transferring control between agents
```python
@handoff
def transfer_to_specialist():
    return specialist_agent
```

#### 3. **Guardrails**
Configurable safety checks for input and output validation
```python
@input_guardrail
def validate_input(input_str: str) -> bool:
    return "harmful" not in input_str.lower()
```

#### 4. **Tracing**
Built-in tracking of agent runs for debugging and optimization
- Automatic tracing to OpenAI platform
- Support for external processors (Logfire, AgentOps, Braintrust)

#### 5. **Runner**
The execution engine that orchestrates agent loops
```python
result = await Runner.run(agent, "Your query here")
```

---

## Installation & Setup

### Basic Installation

```bash
# Core SDK
pip install openai-agents

# With optional dependencies
pip install "openai-agents[voice]"     # For voice support
pip install "openai-agents[litellm]"   # For 100+ model providers
pip install "openai-agents[viz]"       # For visualization
```

### Environment Setup

```bash
# Required for OpenAI models
export OPENAI_API_KEY="your-key-here"

# Optional: For other providers via LiteLLM
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
export MISTRAL_API_KEY="your-key"
```

### Development Setup

```bash
# Clone the repo for examples
git clone https://github.com/openai/openai-agents-python
cd openai-agents-python

# Install with uv (recommended for development)
uv --version  # Ensure uv is installed
make sync     # Install dependencies
make tests    # Run tests
make lint     # Run linter
```

---

## Core Components

### 1. Agent Class

The `Agent` is the core building block:

```python
from agents import Agent

agent = Agent(
    name="Customer Service Bot",
    instructions="""
    You are a helpful customer service representative.
    Always be polite and try to resolve issues.
    If you can't help, transfer to a human agent.
    """,
    model="gpt-4o",  # Default model
    tools=[search_orders, update_status],
    handoffs=[human_agent],
    output_type=CustomerResponse,  # Structured output
    temperature=0.7,
    max_tokens=1000
)
```

**Key Parameters:**
- `name`: Agent identifier
- `instructions`: System prompt/behavior definition
- `model`: LLM model to use (supports 100+ models)
- `tools`: List of functions the agent can call
- `handoffs`: Other agents this agent can transfer to
- `output_type`: Pydantic model for structured outputs
- `temperature`, `max_tokens`: Model parameters

### 2. Runner Class

The `Runner` orchestrates agent execution:

```python
from agents import Runner, RunConfig

# Simple execution
result = await Runner.run(agent, "Help me with my order")
print(result.final_output)

# With configuration
result = await Runner.run(
    agent,
    "Complex query",
    run_config=RunConfig(
        max_turns=10,
        model_provider=CustomProvider(),
        tracing_disabled=False
    )
)

# Synchronous version
result = Runner.run_sync(agent, "Simple query")
```

**Runner Options:**
- `max_turns`: Limit conversation turns
- `model_provider`: Override model provider
- `tracing_disabled`: Disable tracing
- `stream`: Enable streaming responses

### 3. The Agent Loop

Understanding the execution flow:

```
1. Call LLM with message history
2. LLM returns response (may include tool calls)
3. If final output → return and end
4. If handoff → switch agent and goto 1
5. If tool calls → execute tools, append results, goto 1
```

**Final Output Conditions:**
- With `output_type`: When LLM returns structured output
- Without `output_type`: First response without tool calls/handoffs

### 4. Model Settings

Fine-tune model behavior:

```python
from agents import ModelSettings

agent = Agent(
    # ... other params
    model_settings=ModelSettings(
        temperature=0.1,
        max_tokens=2000,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
)
```

---

## Model Providers & Support

### OpenAI Models (Default)

```python
# Using OpenAI Responses API (recommended)
agent = Agent(model="gpt-4o")

# Using Chat Completions API
from agents import set_default_openai_api
set_default_openai_api("chat_completions")

# Custom OpenAI client
from agents import set_default_openai_client
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key="custom-key")
set_default_openai_client(client)
```

### 100+ Models via LiteLLM

```python
# Install LiteLLM support
# pip install "openai-agents[litellm]"

# Anthropic Claude
agent = Agent(model="litellm/anthropic/claude-3-5-sonnet-20240620")

# Google Gemini
agent = Agent(model="litellm/gemini/gemini-2.0-flash")

# Mistral
agent = Agent(model="litellm/mistral/mistral-large-latest")

# AWS Bedrock
agent = Agent(model="litellm/bedrock/anthropic.claude-3-sonnet")

# Local Ollama
agent = Agent(model="litellm/ollama/llama2")

# Any other LiteLLM provider
agent = Agent(model="litellm/provider/model-name")
```

### Custom Model Providers

#### Method 1: Global Client (OpenAI-compatible APIs)

```python
from agents import set_default_openai_client
from openai import AsyncOpenAI

# For any OpenAI-compatible API
client = AsyncOpenAI(
    base_url="https://api.your-provider.com/v1",
    api_key="your-api-key"
)
set_default_openai_client(client)

agent = Agent(model="your-model-name")
```

#### Method 2: Custom Provider (Per-Run)

```python
from agents import ModelProvider, OpenAIChatCompletionsModel, RunConfig
from openai import AsyncOpenAI

class CustomProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        client = AsyncOpenAI(
            base_url="https://api.custom.com/v1",
            api_key="key"
        )
        return OpenAIChatCompletionsModel(
            model=model_name or "default-model",
            openai_client=client
        )

# Use in specific run
result = await Runner.run(
    agent,
    "query",
    run_config=RunConfig(model_provider=CustomProvider())
)
```

#### Method 3: Agent-Level Models

```python
from agents.extensions.models.litellm_model import LitellmModel

# Direct model assignment
agent = Agent(
    model=LitellmModel(
        model="anthropic/claude-3-5-sonnet-20240620",
        api_key="custom-key"
    )
)
```

### Multi-Model Workflows

```python
# Different models for different purposes
fast_agent = Agent(
    name="Triage",
    model="litellm/openai/gpt-4o-mini",  # Fast & cheap
    instructions="Quickly categorize requests"
)

powerful_agent = Agent(
    name="Specialist", 
    model="litellm/anthropic/claude-3-5-sonnet-20240620",  # Powerful
    instructions="Handle complex analysis"
)

# Triage hands off to specialist
triage_agent = Agent(
    handoffs=[powerful_agent],
    # ... other config
)
```

---

## Agent Patterns & Architectures

### 1. Single Agent Pattern

Simple, single-purpose agent:

```python
@function_tool
def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny, 75°F"

weather_agent = Agent(
    name="Weather Assistant",
    instructions="Help users get weather information",
    tools=[get_weather]
)

result = await Runner.run(weather_agent, "What's the weather in NYC?")
```

### 2. Multi-Agent Handoff Pattern

Agents that transfer control:

```python
# Specialist agents
python_agent = Agent(
    name="Python Expert",
    instructions="You are an expert Python programmer"
)

js_agent = Agent(
    name="JavaScript Expert", 
    instructions="You are an expert JavaScript programmer"
)

# Triage agent
triage_agent = Agent(
    name="Programming Triage",
    instructions="""
    Determine which programming language the user needs help with.
    Hand off to the appropriate specialist.
    """,
    handoffs=[python_agent, js_agent]
)

result = await Runner.run(triage_agent, "How do I sort a list in Python?")
```

### 3. Hierarchical Agent Pattern

Parent agent coordinates sub-agents:

```python
# Research agents
web_researcher = Agent(
    name="Web Researcher",
    tools=[web_search, scrape_page],
    instructions="Search and gather information from the web"
)

data_analyst = Agent(
    name="Data Analyst", 
    tools=[analyze_data, create_chart],
    instructions="Analyze data and create visualizations"
)

# Coordinator
research_coordinator = Agent(
    name="Research Coordinator",
    instructions="""
    Coordinate research tasks by delegating to specialists.
    Gather information, analyze it, and provide comprehensive reports.
    """,
    handoffs=[web_researcher, data_analyst]
)
```

### 4. Agent-as-Tool Pattern (Recommended for Complex Systems)

Sub-agents exposed as tools to main agent:

```python
from agents import function_tool

# Create specialized sub-agent
memory_agent = Agent(
    name="Memory Specialist",
    instructions="Manage user memory and information storage",
    tools=[save_memory, search_memory, tag_memory]
)

# Expose as tool to main agent
@function_tool
async def memory_manager_tool(action: str, content: str) -> str:
    """Manage user memories and information storage"""
    result = await Runner.run(memory_agent, f"{action}: {content}")
    return result.final_output

# Main conversational agent
main_agent = Agent(
    name="Personal Assistant",
    instructions="""
    You are a helpful personal assistant with memory capabilities.
    Use the memory_manager_tool when users want to save or recall information.
    """,
    tools=[memory_manager_tool, get_weather, send_email]
)
```

### 5. Pipeline Pattern

Sequential agent processing:

```python
# Stage 1: Data extraction
extractor_agent = Agent(
    name="Data Extractor",
    instructions="Extract structured data from documents",
    output_type=ExtractedData
)

# Stage 2: Data validation  
validator_agent = Agent(
    name="Data Validator",
    instructions="Validate and clean extracted data",
    output_type=ValidatedData
)

# Stage 3: Data enrichment
enricher_agent = Agent(
    name="Data Enricher", 
    instructions="Enrich data with additional information",
    output_type=EnrichedData
)

# Pipeline execution
async def process_document(document: str) -> EnrichedData:
    # Stage 1
    extracted = await Runner.run(extractor_agent, document)
    
    # Stage 2  
    validated = await Runner.run(validator_agent, str(extracted.final_output))
    
    # Stage 3
    enriched = await Runner.run(enricher_agent, str(validated.final_output))
    
    return enriched.final_output
```

---

## Tools & Function Calling

### Basic Function Tools

```python
from agents import function_tool

@function_tool
def calculate_tip(bill_amount: float, tip_percentage: float = 15.0) -> str:
    """Calculate tip amount and total bill"""
    tip = bill_amount * (tip_percentage / 100)
    total = bill_amount + tip
    return f"Tip: ${tip:.2f}, Total: ${total:.2f}"

@function_tool  
def get_stock_price(symbol: str) -> str:
    """Get current stock price for a symbol"""
    # Mock implementation
    return f"Stock {symbol}: $150.25 (+2.3%)"

agent = Agent(
    tools=[calculate_tip, get_stock_price],
    instructions="Help with financial calculations"
)
```

### Advanced Function Tools with Complex Types

```python
from typing import List, Optional
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class SearchQuery(BaseModel):
    query: str
    max_results: int = 5
    domain_filter: Optional[str] = None

@function_tool
def web_search(search_params: SearchQuery) -> List[SearchResult]:
    """Search the web and return structured results"""
    # Implementation here
    return [
        SearchResult(
            title="Example Result",
            url="https://example.com", 
            snippet="Example snippet..."
        )
    ]

agent = Agent(
    tools=[web_search],
    instructions="Search the web for information"
)
```

### Built-in Tools

The SDK provides several built-in tools:

```python
from agents import (
    CodeInterpreterTool,
    FileSearchTool, 
    WebSearchTool,
    ImageGenerationTool,
    ComputerTool,
    LocalShellTool
)

agent = Agent(
    tools=[
        CodeInterpreterTool(),
        FileSearchTool(),
        WebSearchTool(),
        ImageGenerationTool(),
        ComputerTool(),  # Control computer interface
        LocalShellTool()  # Execute shell commands
    ]
)
```

### Tool Error Handling

```python
@function_tool
def risky_operation(data: str) -> str:
    """An operation that might fail"""
    try:
        # Some risky operation
        result = process_data(data)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# Custom error handler
def custom_error_handler(error: Exception) -> str:
    return f"Tool failed gracefully: {error}"

agent = Agent(
    tools=[risky_operation],
    # Use custom error handling
    default_tool_error_function=custom_error_handler
)
```

---

## Handoffs & Multi-Agent Systems

### Basic Handoffs

```python
from agents import handoff

# Define target agents
support_agent = Agent(
    name="Support Specialist",
    instructions="Handle customer support issues"
)

sales_agent = Agent(
    name="Sales Specialist", 
    instructions="Handle sales inquiries and quotes"
)

# Triage agent with handoffs
@handoff
def transfer_to_support():
    """Transfer to customer support for technical issues"""
    return support_agent

@handoff  
def transfer_to_sales():
    """Transfer to sales team for purchase inquiries"""
    return sales_agent

triage_agent = Agent(
    name="Customer Triage",
    instructions="""
    Analyze customer inquiries and route appropriately:
    - Technical issues → transfer_to_support()
    - Sales questions → transfer_to_sales()
    """,
    handoffs=[transfer_to_support, transfer_to_sales]
)
```

### Handoff with Context

```python
from agents import HandoffInputData

@handoff
def escalate_to_manager(
    issue_summary: str,
    customer_tier: str = "standard"
) -> HandoffInputData:
    """Escalate complex issues to manager with context"""
    return HandoffInputData(
        agent=manager_agent,
        input=f"Escalated issue from {customer_tier} customer: {issue_summary}"
    )

agent = Agent(
    handoffs=[escalate_to_manager],
    instructions="Handle customer issues, escalate complex ones"
)
```

### Conditional Handoffs

```python
from agents import HandoffInputFilter

# Only handoff during business hours
@HandoffInputFilter
def business_hours_only(input_data: str) -> bool:
    import datetime
    now = datetime.datetime.now()
    return 9 <= now.hour < 17  # 9 AM to 5 PM

human_agent = Agent(
    name="Human Agent",
    instructions="Handle escalated issues"
)

bot_agent = Agent(
    handoffs=[
        handoff(
            target=human_agent,
            filter=business_hours_only
        )
    ]
)
```

### Multi-Agent Conversation Patterns

#### Round-Robin Pattern

```python
async def round_robin_discussion(topic: str, agents: List[Agent], rounds: int = 3):
    """Have multiple agents discuss a topic in rounds"""
    conversation = f"Topic: {topic}\n"
    
    for round_num in range(rounds):
        print(f"\n--- Round {round_num + 1} ---")
        for agent in agents:
            result = await Runner.run(agent, conversation)
            conversation += f"\n{agent.name}: {result.final_output}"
            print(f"{agent.name}: {result.final_output}")
    
    return conversation

# Usage
experts = [
    Agent(name="Economist", instructions="Analyze from economic perspective"),
    Agent(name="Sociologist", instructions="Analyze from social perspective"),
    Agent(name="Technologist", instructions="Analyze from tech perspective")
]

discussion = await round_robin_discussion(
    "Impact of AI on future jobs", 
    experts, 
    rounds=2
)
```

#### Debate Pattern

```python
async def agent_debate(topic: str, agent_a: Agent, agent_b: Agent, moderator: Agent):
    """Moderate a debate between two agents"""
    
    # Initial positions
    result_a = await Runner.run(agent_a, f"Present your position on: {topic}")
    result_b = await Runner.run(agent_b, f"Present your position on: {topic}")
    
    debate_log = f"Topic: {topic}\n"
    debate_log += f"{agent_a.name}: {result_a.final_output}\n"
    debate_log += f"{agent_b.name}: {result_b.final_output}\n"
    
    # Rebuttals
    for round_num in range(3):
        # A responds to B
        response_a = await Runner.run(
            agent_a, 
            f"Respond to {agent_b.name}'s argument: {result_b.final_output}"
        )
        debate_log += f"\n{agent_a.name} (Round {round_num+1}): {response_a.final_output}"
        
        # B responds to A  
        response_b = await Runner.run(
            agent_b,
            f"Respond to {agent_a.name}'s argument: {response_a.final_output}"
        )
        debate_log += f"\n{agent_b.name} (Round {round_num+1}): {response_b.final_output}"
    
    # Moderator summary
    summary = await Runner.run(moderator, f"Summarize this debate:\n{debate_log}")
    return summary.final_output
```

---

## Guardrails & Safety

### Input Guardrails

```python
from agents import input_guardrail, InputGuardrailResult

@input_guardrail
def content_filter(input_str: str) -> InputGuardrailResult:
    """Filter inappropriate content"""
    harmful_keywords = ["violence", "harmful", "dangerous"]
    
    if any(keyword in input_str.lower() for keyword in harmful_keywords):
        return InputGuardrailResult(
            allowed=False,
            message="Content blocked: Contains inappropriate material"
        )
    
    return InputGuardrailResult(allowed=True)

@input_guardrail  
def length_limit(input_str: str) -> InputGuardrailResult:
    """Limit input length"""
    if len(input_str) > 1000:
        return InputGuardrailResult(
            allowed=False,
            message="Input too long. Please limit to 1000 characters."
        )
    return InputGuardrailResult(allowed=True)

agent = Agent(
    input_guardrails=[content_filter, length_limit],
    instructions="Helpful assistant with safety measures"
)
```

### Output Guardrails

```python
from agents import output_guardrail, OutputGuardrailResult

@output_guardrail
def response_filter(output: str) -> OutputGuardrailResult:
    """Filter agent responses"""
    if "confidential" in output.lower():
        return OutputGuardrailResult(
            allowed=False,
            replacement="I cannot share confidential information."
        )
    return OutputGuardrailResult(allowed=True)

@output_guardrail
def ensure_helpfulness(output: str) -> OutputGuardrailResult:
    """Ensure responses are helpful"""
    if len(output.strip()) < 10:
        return OutputGuardrailResult(
            allowed=False,
            replacement="I apologize, but I need to provide a more helpful response."
        )
    return OutputGuardrailResult(allowed=True)

agent = Agent(
    output_guardrails=[response_filter, ensure_helpfulness],
    instructions="Provide helpful and safe responses"
)
```

### Advanced Guardrail Patterns

```python
# Rate limiting guardrail
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_minutes: int = 5):
        self.max_requests = max_requests
        self.window = timedelta(minutes=window_minutes)
        self.requests = defaultdict(list)
    
    @input_guardrail
    def rate_limit_check(self, input_str: str) -> InputGuardrailResult:
        user_id = "default_user"  # In real app, extract from context
        now = datetime.now()
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return InputGuardrailResult(
                allowed=False,
                message=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window.total_seconds()/60} minutes."
            )
        
        self.requests[user_id].append(now)
        return InputGuardrailResult(allowed=True)

rate_limiter = RateLimiter(max_requests=5, window_minutes=1)

agent = Agent(
    input_guardrails=[rate_limiter.rate_limit_check],
    instructions="Rate-limited assistant"
)
```

---

## Tracing & Debugging

### Built-in Tracing

Tracing is enabled by default and sends data to OpenAI platform:

```python
from agents import Agent, Runner

# Tracing enabled by default
agent = Agent(name="Traced Agent")
result = await Runner.run(agent, "Hello")

# Disable tracing
from agents import set_tracing_disabled
set_tracing_disabled(True)

# Custom tracing API key
from agents import set_tracing_export_api_key
set_tracing_export_api_key("your-tracing-key")
```

### Custom Tracing Processors

#### Logfire Integration

```bash
pip install logfire
```

```python
import logfire
from agents import add_trace_processor

# Configure Logfire
logfire.configure(token="your-logfire-token")

# Add Logfire processor
add_trace_processor(logfire.LogfireTracingProcessor())

agent = Agent(name="Logged Agent")
```

#### Custom Trace Processor

```python
from agents import TracingProcessor, Trace, add_trace_processor

class CustomTraceProcessor(TracingProcessor):
    def process_trace(self, trace: Trace) -> None:
        """Custom trace processing"""
        print(f"Trace ID: {trace.id}")
        print(f"Duration: {trace.duration}")
        print(f"Spans: {len(trace.spans)}")
        
        # Log to your system
        for span in trace.spans:
            print(f"  Span: {span.name} ({span.duration}ms)")
            if hasattr(span.span_data, 'usage'):
                print(f"    Tokens: {span.span_data.usage}")

# Add custom processor
add_trace_processor(CustomTraceProcessor())
```

### Custom Spans

```python
from agents import custom_span, function_span

@function_tool
def complex_calculation(data: str) -> str:
    """Tool with custom tracing"""
    
    with custom_span("data_preprocessing") as span:
        span.span_data.metadata = {"input_length": len(data)}
        processed_data = preprocess(data)
    
    with custom_span("main_calculation") as span:
        result = calculate(processed_data)
        span.span_data.metadata = {"result_size": len(result)}
    
    return result

# Function-level tracing
@function_span("my_function")
def my_function(param: str) -> str:
    # Function automatically traced
    return f"Processed: {param}"
```

### Debug Mode

```python
from agents import enable_verbose_stdout_logging

# Enable verbose logging for debugging
enable_verbose_stdout_logging()

# Now all agent interactions will be logged to stdout
agent = Agent(name="Debug Agent")
result = await Runner.run(agent, "Debug this")
```

---

## Advanced Examples

### 1. Customer Service Agent System

```python
from agents import Agent, handoff, function_tool
from typing import List, Optional
from pydantic import BaseModel

# Data models
class TicketInfo(BaseModel):
    ticket_id: str
    status: str
    priority: str
    description: str

class CustomerInfo(BaseModel):
    customer_id: str
    tier: str
    name: str
    email: str

# Tools
@function_tool
def lookup_customer(email: str) -> CustomerInfo:
    """Look up customer information"""
    # Mock implementation
    return CustomerInfo(
        customer_id="CUST123",
        tier="premium",
        name="John Doe", 
        email=email
    )

@function_tool
def search_tickets(customer_id: str) -> List[TicketInfo]:
    """Search customer support tickets"""
    # Mock implementation
    return [
        TicketInfo(
            ticket_id="TKT456",
            status="open",
            priority="high",
            description="Login issues"
        )
    ]

@function_tool
def create_ticket(
    customer_id: str, 
    description: str, 
    priority: str = "medium"
) -> TicketInfo:
    """Create a new support ticket"""
    import uuid
    return TicketInfo(
        ticket_id=f"TKT{uuid.uuid4().hex[:6].upper()}",
        status="open",
        priority=priority,
        description=description
    )

# Specialized agents
technical_agent = Agent(
    name="Technical Support",
    instructions="""
    You are a technical support specialist.
    Help customers with technical issues using available tools.
    Escalate complex issues to Level 2 support.
    """,
    tools=[lookup_customer, search_tickets, create_ticket]
)

billing_agent = Agent(
    name="Billing Support",
    instructions="""
    You are a billing specialist.
    Help customers with billing questions and payment issues.
    """,
    tools=[lookup_customer, search_tickets]
)

# Handoff functions
@handoff
def transfer_to_technical():
    """Transfer to technical support for technical issues"""
    return technical_agent

@handoff
def transfer_to_billing():
    """Transfer to billing for payment and account issues"""
    return billing_agent

# Main triage agent
triage_agent = Agent(
    name="Customer Service Triage",
    instructions="""
    You are a customer service triage agent.
    
    Analyze customer inquiries and route them appropriately:
    - Technical problems (login, bugs, features) → transfer_to_technical()
    - Billing questions (payments, charges, refunds) → transfer_to_billing()
    
    Always be helpful and professional.
    """,
    tools=[lookup_customer],
    handoffs=[transfer_to_technical, transfer_to_billing]
)

# Usage
async def handle_customer_inquiry(inquiry: str, customer_email: str):
    result = await Runner.run(
        triage_agent, 
        f"Customer {customer_email} asks: {inquiry}"
    )
    return result.final_output
```

### 2. Research & Analysis Pipeline

```python
from agents import Agent, function_tool, Runner
from pydantic import BaseModel
from typing import List

# Data models
class ResearchQuery(BaseModel):
    query: str
    domain: str
    depth: str  # "shallow", "medium", "deep"

class ResearchResult(BaseModel):
    sources: List[str]
    summary: str
    key_findings: List[str]
    confidence_score: float

class AnalysisResult(BaseModel):
    insights: List[str]
    recommendations: List[str]
    risks: List[str]
    opportunities: List[str]

# Research tools
@function_tool
def web_search(query: str, max_results: int = 5) -> List[str]:
    """Search the web for information"""
    # Mock implementation
    return [
        f"Article about {query} from source1.com",
        f"Research paper on {query} from academic.edu",
        f"News article about {query} from news.com"
    ]

@function_tool  
def analyze_sentiment(text: str) -> str:
    """Analyze sentiment of text"""
    # Mock implementation
    return "positive"

@function_tool
def extract_entities(text: str) -> List[str]:
    """Extract named entities from text"""
    # Mock implementation
    return ["Company A", "Technology B", "Market C"]

# Specialized agents
research_agent = Agent(
    name="Research Specialist",
    instructions="""
    You are a research specialist. Gather comprehensive information 
    on topics using web search and analysis tools.
    Provide thorough summaries with source citations.
    """,
    tools=[web_search, extract_entities],
    output_type=ResearchResult
)

analysis_agent = Agent(
    name="Analysis Specialist", 
    instructions="""
    You are an analysis specialist. Take research findings and
    provide strategic insights, recommendations, and risk assessments.
    """,
    tools=[analyze_sentiment],
    output_type=AnalysisResult
)

synthesis_agent = Agent(
    name="Synthesis Specialist",
    instructions="""
    You synthesize research and analysis into executive summaries
    and actionable recommendations.
    """
)

# Orchestrator
async def comprehensive_research(query: ResearchQuery) -> str:
    """Run a complete research and analysis pipeline"""
    
    # Stage 1: Research
    print("🔍 Starting research phase...")
    research_result = await Runner.run(
        research_agent,
        f"Research: {query.query} in {query.domain} domain with {query.depth} depth"
    )
    
    # Stage 2: Analysis
    print("📊 Starting analysis phase...")
    analysis_result = await Runner.run(
        analysis_agent,
        f"Analyze this research: {research_result.final_output}"
    )
    
    # Stage 3: Synthesis
    print("📝 Starting synthesis phase...")
    synthesis_result = await Runner.run(
        synthesis_agent,
        f"""
        Create an executive summary combining:
        
        Research: {research_result.final_output}
        Analysis: {analysis_result.final_output}
        
        Provide actionable insights and recommendations.
        """
    )
    
    return synthesis_result.final_output

# Usage
query = ResearchQuery(
    query="impact of artificial intelligence on healthcare",
    domain="healthcare", 
    depth="deep"
)

result = await comprehensive_research(query)
print(result)
```

### 3. Memory-Enhanced Personal Assistant

```python
from agents import Agent, function_tool, Runner
from datetime import datetime
from typing import Dict, List, Optional
import json

# Memory storage (in production, use proper database)
memory_store: Dict[str, Dict] = {}

# Memory tools
@function_tool
def save_memory(
    key: str,
    content: str,
    tags: Optional[List[str]] = None,
    category: str = "general"
) -> str:
    """Save information to memory with tags and category"""
    memory_store[key] = {
        "content": content,
        "tags": tags or [],
        "category": category,
        "timestamp": datetime.now().isoformat(),
        "access_count": 0
    }
    return f"Saved memory '{key}' in category '{category}'"

@function_tool
def search_memory(
    query: str,
    category: Optional[str] = None,
    limit: int = 5
) -> List[Dict]:
    """Search memories by content, tags, or category"""
    results = []
    
    for key, memory in memory_store.items():
        # Simple text search (in production, use proper search)
        if query.lower() in memory["content"].lower():
            if category is None or memory["category"] == category:
                memory["key"] = key
                results.append(memory)
                # Update access count
                memory_store[key]["access_count"] += 1
    
    return results[:limit]

@function_tool
def list_categories() -> List[str]:
    """List all memory categories"""
    categories = set()
    for memory in memory_store.values():
        categories.add(memory["category"])
    return list(categories)

@function_tool
def get_recent_memories(limit: int = 10) -> List[Dict]:
    """Get most recently saved memories"""
    sorted_memories = sorted(
        memory_store.items(),
        key=lambda x: x[1]["timestamp"],
        reverse=True
    )
    
    results = []
    for key, memory in sorted_memories[:limit]:
        memory_copy = memory.copy()
        memory_copy["key"] = key
        results.append(memory_copy)
    
    return results

# Memory specialist agent
memory_agent = Agent(
    name="Memory Specialist",
    instructions="""
    You are a memory management specialist. Help users:
    - Save important information with appropriate tags and categories
    - Search and retrieve saved information
    - Organize and categorize memories
    - Suggest relevant past information based on current context
    
    Always tag memories appropriately and use meaningful categories.
    When searching, be flexible and try different keywords if needed.
    """,
    tools=[save_memory, search_memory, list_categories, get_recent_memories]
)

# Expose memory agent as tool
@function_tool
async def memory_manager_tool(action: str, query: str = "") -> str:
    """
    Manage user memories and information storage.
    
    Actions:
    - save: Save new information
    - search: Search existing memories  
    - recall: Get recent or relevant memories
    - organize: List categories and organize memories
    """
    prompt = f"Action: {action}\nQuery: {query}"
    result = await Runner.run(memory_agent, prompt)
    return result.final_output

# Other assistant tools
@function_tool
def get_current_time() -> str:
    """Get current date and time"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@function_tool
def set_reminder(message: str, time: str) -> str:
    """Set a reminder (mock implementation)"""
    return f"Reminder set: '{message}' for {time}"

# Main personal assistant
personal_assistant = Agent(
    name="Personal Assistant",
    instructions="""
    You are a helpful personal assistant with memory capabilities.
    
    Key behaviors:
    - Use memory_manager_tool to save important information users share
    - Search memories to provide context-aware responses
    - Proactively recall relevant information from past conversations
    - Help users organize and find their stored information
    
    When users share:
    - Personal preferences → save to "preferences" category
    - Important dates → save to "dates" category  
    - Work information → save to "work" category
    - Goals and plans → save to "goals" category
    
    Always be proactive about connecting current conversations to past information.
    """,
    tools=[memory_manager_tool, get_current_time, set_reminder]
)

# Usage examples
async def demo_memory_assistant():
    # User shares preference
    result1 = await Runner.run(
        personal_assistant,
        "I really love Italian food, especially pasta carbonara. My favorite restaurant is Mario's downtown."
    )
    print("Assistant:", result1.final_output)
    
    # Later conversation about restaurants
    result2 = await Runner.run(
        personal_assistant,
        "Can you recommend a good place for dinner tonight?"
    )
    print("Assistant:", result2.final_output)
    
    # User asks about past preferences
    result3 = await Runner.run(
        personal_assistant, 
        "What do you know about my food preferences?"
    )
    print("Assistant:", result3.final_output)

# Run demo
await demo_memory_assistant()
```

---

## Best Practices & Recommendations

### 1. Agent Design Principles

#### Single Responsibility
```python
# ✅ Good: Focused agent
weather_agent = Agent(
    name="Weather Assistant",
    instructions="Provide accurate weather information and forecasts",
    tools=[get_weather, get_forecast]
)

# ❌ Avoid: Jack-of-all-trades agent
everything_agent = Agent(
    name="Everything Agent", 
    instructions="Handle weather, cooking, finance, tech support, and travel",
    tools=[get_weather, recipe_search, stock_prices, debug_code, book_flights]
)
```

#### Clear Instructions
```python
# ✅ Good: Specific, actionable instructions
agent = Agent(
    instructions="""
    You are a customer support agent for a SaaS platform.
    
    Your responsibilities:
    1. Help users with account issues and billing questions
    2. Provide step-by-step troubleshooting for technical problems
    3. Escalate complex issues to human agents using transfer_to_human()
    4. Always be polite, professional, and solution-oriented
    
    Guidelines:
    - Ask clarifying questions when issues are unclear
    - Provide specific action steps, not just general advice
    - Include relevant links and documentation when helpful
    - If you cannot resolve an issue, explain why and suggest next steps
    """
)

# ❌ Avoid: Vague instructions
agent = Agent(
    instructions="Be helpful and answer questions"
)
```

### 2. Error Handling & Resilience

#### Graceful Tool Failures
```python
@function_tool
def external_api_call(query: str) -> str:
    """Call external API with proper error handling"""
    try:
        response = requests.get(f"https://api.example.com/search?q={query}", timeout=10)
        response.raise_for_status()
        return response.json()["result"]
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again later."
    except requests.exceptions.ConnectionError:
        return "Error: Unable to connect to service. Please check your internet connection."
    except requests.exceptions.HTTPError as e:
        return f"Error: Service returned {e.response.status_code}. Please try again later."
    except Exception as e:
        return f"Error: Unexpected issue occurred - {str(e)}"
```

#### Circuit Breaker Pattern
```python
from datetime import datetime, timedelta
from typing import Dict

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = "HALF_OPEN"
            else:
                return "Service temporarily unavailable"
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e

# Usage
breaker = CircuitBreaker()

@function_tool
def protected_api_call(query: str) -> str:
    """API call protected by circuit breaker"""
    return breaker.call(unreliable_api_function, query)
```

### 3. Performance Optimization

#### Efficient Tool Selection
```python
# ✅ Good: Specific tools with clear purposes
@function_tool
def search_products(query: str, category: str = "all") -> List[Dict]:
    """Search for products in specific category"""
    pass

@function_tool  
def get_product_details(product_id: str) -> Dict:
    """Get detailed information for specific product"""
    pass

# ❌ Avoid: One tool that does everything
@function_tool
def product_operations(action: str, **kwargs) -> str:
    """Handle all product-related operations"""
    # This forces the LLM to always consider this tool
    # and makes the function signature unclear
    pass
```

#### Caching Strategies
```python
from functools import lru_cache
import asyncio

# Synchronous caching
@lru_cache(maxsize=100)
def expensive_computation(data: str) -> str:
    """Cached expensive operation"""
    # Expensive computation here
    return f"Result for {data}"

# Async caching
class AsyncCache:
    def __init__(self, maxsize: int = 100):
        self.cache = {}
        self.maxsize = maxsize
    
    async def get_or_compute(self, key: str, compute_func, *args):
        if key in self.cache:
            return self.cache[key]
        
        result = await compute_func(*args)
        
        if len(self.cache) >= self.maxsize:
            # Simple LRU: remove oldest
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = result
        return result

cache = AsyncCache()

@function_tool
async def cached_api_call(query: str) -> str:
    """Cached API call"""
    return await cache.get_or_compute(
        f"api_{query}",
        actual_api_call,
        query
    )
```

#### Parallel Tool Execution
```python
import asyncio

@function_tool
async def gather_multiple_sources(queries: List[str]) -> Dict[str, str]:
    """Fetch data from multiple sources in parallel"""
    
    async def fetch_source(query: str) -> str:
        # Simulate API call
        await asyncio.sleep(1)
        return f"Data for {query}"
    
    # Execute all requests in parallel
    tasks = [fetch_source(query) for query in queries]
    results = await asyncio.gather(*tasks)
    
    return dict(zip(queries, results))
```

### 4. Security Best Practices

#### Input Validation
```python
@function_tool
def secure_file_operation(filename: str, operation: str) -> str:
    """Secure file operations with validation"""
    import os
    import re
    
    # Validate filename
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        return "Error: Invalid filename. Only alphanumeric, dots, dashes, and underscores allowed."
    
    # Prevent path traversal
    if '..' in filename or filename.startswith('/'):
        return "Error: Invalid path. Path traversal not allowed."
    
    # Validate operation
    allowed_operations = ['read', 'write', 'delete']
    if operation not in allowed_operations:
        return f"Error: Invalid operation. Allowed: {allowed_operations}"
    
    # Proceed with validated inputs
    safe_path = os.path.join("safe_directory", filename)
    # ... perform operation
    
    return f"Successfully performed {operation} on {filename}"
```

#### Sensitive Data Handling
```python
import re

@function_tool
def process_user_data(data: str) -> str:
    """Process user data with PII protection"""
    
    # Redact potential PII
    # Email addresses
    data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', data)
    
    # Phone numbers (US format)
    data = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', data)
    
    # SSN pattern
    data = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', data)
    
    # Credit card numbers
    data = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', data)
    
    return f"Processed data: {data}"
```

### 5. Testing Strategies

#### Unit Testing Agents
```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_weather_agent():
    """Test weather agent behavior"""
    
    # Mock the weather API
    with patch('weather_api.get_weather') as mock_weather:
        mock_weather.return_value = "Sunny, 75°F"
        
        agent = Agent(
            name="Weather Bot",
            tools=[get_weather],
            instructions="Provide weather information"
        )
        
        result = await Runner.run(agent, "What's the weather in NYC?")
        
        # Verify API was called
        mock_weather.assert_called_once()
        
        # Verify response contains weather info
        assert "75°F" in result.final_output
        assert "Sunny" in result.final_output

@pytest.mark.asyncio
async def test_agent_handoff():
    """Test agent handoff behavior"""
    
    specialist_agent = Agent(name="Specialist")
    
    @handoff
    def transfer_to_specialist():
        return specialist_agent
    
    triage_agent = Agent(
        name="Triage",
        instructions="Transfer complex issues to specialist",
        handoffs=[transfer_to_specialist]
    )
    
    result = await Runner.run(triage_agent, "Complex technical issue")
    
    # Should have transferred to specialist
    assert result.agent.name == "Specialist"
```

#### Integration Testing
```python
@pytest.mark.asyncio
async def test_full_customer_service_flow():
    """Test complete customer service workflow"""
    
    # Setup test data
    test_customer = {
        "email": "test@example.com",
        "tier": "premium"
    }
    
    # Mock external services
    with patch('customer_db.lookup') as mock_lookup:
        mock_lookup.return_value = test_customer
        
        # Test the flow
        result = await handle_customer_inquiry(
            "I can't log into my account",
            "test@example.com"
        )
        
        # Verify customer was looked up
        mock_lookup.assert_called_with("test@example.com")
        
        # Verify appropriate response
        assert "login" in result.lower()
        assert "help" in result.lower()
```

---

## Troubleshooting & Common Issues

### 1. Model-Related Issues

#### API Key Problems
```python
# ✅ Proper error handling for API keys
try:
    result = await Runner.run(agent, "Hello")
except Exception as e:
    if "authentication" in str(e).lower():
        print("❌ API Key Issue:")
        print("- Check OPENAI_API_KEY environment variable")
        print("- Verify key is valid and has sufficient credits")
        print("- For other providers, check respective API key env vars")
    else:
        print(f"❌ Other error: {e}")
```

#### Model Compatibility
```python
# Check model support
try:
    agent = Agent(model="litellm/unsupported/model")
    result = await Runner.run(agent, "test")
except Exception as e:
    print(f"Model not supported: {e}")
    print("Check https://docs.litellm.ai/docs/providers for supported models")
```

#### Rate Limiting
```python
from agents import Runner, RunConfig
import asyncio

async def rate_limited_requests(requests: List[str]):
    """Handle multiple requests with rate limiting"""
    results = []
    
    for i, request in enumerate(requests):
        try:
            result = await Runner.run(agent, request)
            results.append(result.final_output)
            
            # Add delay to respect rate limits
            if i < len(requests) - 1:
                await asyncio.sleep(1)
                
        except Exception as e:
            if "rate limit" in str(e).lower():
                print(f"Rate limited, waiting 60 seconds...")
                await asyncio.sleep(60)
                # Retry the request
                result = await Runner.run(agent, request)
                results.append(result.final_output)
            else:
                raise e
    
    return results
```

### 2. Tool-Related Issues

#### Tool Not Being Called
```python
# ✅ Good: Clear tool description and parameters
@function_tool
def search_database(
    query: str,
    table: str = "products",
    limit: int = 10
) -> List[Dict]:
    """
    Search the database for records matching the query.
    
    Args:
        query: Search term or phrase to look for
        table: Database table to search (products, users, orders)
        limit: Maximum number of results to return (1-100)
    
    Returns:
        List of matching records with all fields
    """
    # Implementation
    pass

# ❌ Avoid: Vague tool description
@function_tool
def search(q: str) -> str:
    """Search for stuff"""
    pass
```

#### Tool Execution Errors
```python
@function_tool
def robust_tool(data: str) -> str:
    """Tool with comprehensive error handling"""
    try:
        # Validate input
        if not data or not isinstance(data, str):
            return "Error: Invalid input. Please provide a non-empty string."
        
        if len(data) > 1000:
            return "Error: Input too long. Please limit to 1000 characters."
        
        # Process data
        result = process_data(data)
        
        if not result:
            return "Warning: No results found for the given input."
        
        return f"Success: {result}"
        
    except ValueError as e:
        return f"Input Error: {str(e)}"
    except ConnectionError as e:
        return f"Connection Error: Unable to connect to external service. {str(e)}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}. Please contact support if this persists."
```

### 3. Agent Behavior Issues

#### Agent Not Following Instructions
```python
# ✅ Good: Specific, actionable instructions
agent = Agent(
    instructions="""
    You are a helpful assistant that ALWAYS follows these rules:
    
    1. ALWAYS respond in a friendly, professional tone
    2. If asked about something you cannot help with, explain why and suggest alternatives
    3. When using tools, ALWAYS explain what you're doing before calling the tool
    4. If a tool returns an error, acknowledge it and suggest next steps
    5. NEVER make up information - only use data from tools or general knowledge
    
    Response format:
    - For simple questions: Direct answer with explanation
    - For complex tasks: Break down steps and explain your process
    - For errors: Acknowledge the issue and provide helpful alternatives
    """
)

# ❌ Avoid: Generic instructions
agent = Agent(
    instructions="Be helpful and answer questions well"
)
```

#### Infinite Tool Loops
```python
# Prevent infinite loops with max_turns
result = await Runner.run(
    agent,
    "Query that might cause loops",
    run_config=RunConfig(max_turns=10)  # Limit conversation turns
)

# Or design tools to be more deterministic
@function_tool
def search_with_state(query: str, page: int = 1) -> str:
    """Search with pagination to prevent endless searching"""
    if page > 5:  # Limit pages
        return "Search completed. No more results available."
    
    results = search_api(query, page)
    if not results:
        return "No results found. Search completed."
    
    return f"Found {len(results)} results on page {page}: {results}"
```

### 4. Performance Issues

#### Slow Response Times
```python
# Profile agent performance
import time
from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()

start_time = time.time()
result = await Runner.run(agent, "Complex query")
end_time = time.time()

print(f"Agent execution took {end_time - start_time:.2f} seconds")

# Optimize by reducing tool count
fast_agent = Agent(
    tools=[essential_tool_1, essential_tool_2],  # Only necessary tools
    instructions="Be concise and efficient"
)
```

#### Memory Usage
```python
# Monitor memory usage
import psutil
import os

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

before_memory = get_memory_usage()
result = await Runner.run(agent, "Memory intensive task")
after_memory = get_memory_usage()

print(f"Memory used: {after_memory - before_memory:.2f} MB")
```

### 5. Debugging Techniques

#### Step-by-Step Debugging
```python
from agents import enable_verbose_stdout_logging, set_tracing_disabled

# Enable detailed logging
enable_verbose_stdout_logging()

# Disable tracing for cleaner logs during debugging
set_tracing_disabled(True)

# Add debug prints in tools
@function_tool
def debug_tool(input_data: str) -> str:
    """Tool with debug information"""
    print(f"🔧 Tool called with: {input_data}")
    
    result = process_data(input_data)
    print(f"🔧 Tool result: {result}")
    
    return result

# Test with simple inputs first
simple_result = await Runner.run(agent, "Simple test")
print(f"Simple test result: {simple_result.final_output}")
```

#### Isolation Testing
```python
# Test individual components
async def test_tool_isolation():
    """Test tools in isolation"""
    
    # Test tool directly
    tool_result = my_tool("test input")
    print(f"Direct tool call: {tool_result}")
    
    # Test agent with single tool
    simple_agent = Agent(
        name="Test Agent",
        instructions="Only use the provided tool",
        tools=[my_tool]
    )
    
    agent_result = await Runner.run(simple_agent, "Use the tool with 'test input'")
    print(f"Agent with tool: {agent_result.final_output}")
```

---

## Production Deployment

### 1. Environment Configuration

#### Production Environment Setup
```python
import os
from agents import set_default_openai_client, set_tracing_disabled
from openai import AsyncOpenAI

def setup_production_environment():
    """Configure agents for production deployment"""
    
    # Use environment-specific configuration
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Production OpenAI client with error handling
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=3,
            timeout=30.0
        )
        set_default_openai_client(client)
        
        # Configure tracing for production
        tracing_key = os.getenv("OPENAI_TRACING_KEY")
        if tracing_key:
            set_tracing_export_api_key(tracing_key)
        else:
            set_tracing_disabled(True)
    
    elif environment == "development":
        # Development settings
        set_tracing_disabled(False)  # Enable for debugging
    
    else:
        raise ValueError(f"Unknown environment: {environment}")

# Call during app startup
setup_production_environment()
```

#### Configuration Management
```python
from pydantic import BaseSettings
from typing import Optional

class AgentConfig(BaseSettings):
    """Agent configuration with environment variable support"""
    
    # API Keys
    openai_api_key: str
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Model Settings
    default_model: str = "gpt-4o"
    default_temperature: float = 0.7
    default_max_tokens: int = 1000
    
    # Performance Settings
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    max_retries: int = 3
    
    # Feature Flags
    tracing_enabled: bool = True
    debug_mode: bool = False
    
    # Security
    rate_limit_per_minute: int = 60
    max_input_length: int = 10000
    
    class Config:
        env_file = ".env"
        env_prefix = "AGENT_"

# Usage
config = AgentConfig()

agent = Agent(
    model=config.default_model,
    temperature=config.default_temperature,
    max_tokens=config.default_max_tokens
)
```

### 2. Scalability Patterns

#### Connection Pooling
```python
import asyncio
from typing import Dict, Any
import aiohttp

class AgentPool:
    """Pool of agents for handling concurrent requests"""
    
    def __init__(self, agent_config: Dict[str, Any], pool_size: int = 10):
        self.agent_config = agent_config
        self.pool_size = pool_size
        self.semaphore = asyncio.Semaphore(pool_size)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def process_request(self, user_input: str, context: Dict = None) -> str:
        """Process request with connection pooling"""
        async with self.semaphore:  # Limit concurrent requests
            agent = Agent(**self.agent_config)
            
            # Add context to input if provided
            if context:
                enhanced_input = f"Context: {context}\nUser: {user_input}"
            else:
                enhanced_input = user_input
            
            result = await Runner.run(agent, enhanced_input)
            return result.final_output

# Usage
async def main():
    agent_config = {
        "name": "Production Agent",
        "model": "gpt-4o",
        "instructions": "You are a helpful assistant",
        "tools": [get_weather, search_database]
    }
    
    async with AgentPool(agent_config, pool_size=5) as pool:
        # Process multiple requests concurrently
        tasks = [
            pool.process_request("What's the weather?"),
            pool.process_request("Search for products"),
            pool.process_request("Help with account")
        ]
        
        results = await asyncio.gather(*tasks)
        for i, result in enumerate(results):
            print(f"Request {i+1}: {result}")
```

#### Load Balancing
```python
import random
from typing import List
from agents import Agent, Runner

class LoadBalancedAgentCluster:
    """Distribute requests across multiple agent instances"""
    
    def __init__(self, agent_configs: List[Dict]):
        self.agents = [Agent(**config) for config in agent_configs]
        self.request_counts = [0] * len(self.agents)
    
    def get_least_loaded_agent(self) -> Agent:
        """Get agent with fewest current requests"""
        min_index = min(range(len(self.request_counts)), 
                       key=lambda i: self.request_counts[i])
        return self.agents[min_index], min_index
    
    async def process_request(self, user_input: str) -> str:
        """Process request with load balancing"""
        agent, agent_index = self.get_least_loaded_agent()
        
        try:
            self.request_counts[agent_index] += 1
            result = await Runner.run(agent, user_input)
            return result.final_output
        finally:
            self.request_counts[agent_index] -= 1
    
    def get_stats(self) -> Dict:
        """Get cluster statistics"""
        return {
            "total_agents": len(self.agents),
            "request_counts": self.request_counts.copy(),
            "total_requests": sum(self.request_counts)
        }

# Usage
cluster_configs = [
    {
        "name": "Agent-1",
        "model": "gpt-4o",
        "instructions": "You are assistant #1"
    },
    {
        "name": "Agent-2", 
        "model": "gpt-4o",
        "instructions": "You are assistant #2"
    }
]

cluster = LoadBalancedAgentCluster(cluster_configs)
result = await cluster.process_request("Hello!")
```

### 3. Monitoring & Observability

#### Health Checks
```python
from datetime import datetime
import asyncio

class AgentHealthChecker:
    """Monitor agent health and performance"""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.health_status = {
            "status": "unknown",
            "last_check": None,
            "response_time": None,
            "error_count": 0,
            "success_count": 0
        }
    
    async def health_check(self) -> Dict:
        """Perform health check on agent"""
        start_time = datetime.now()
        
        try:
            # Simple health check query
            result = await Runner.run(
                self.agent,
                "Health check - please respond with 'OK'",
                run_config=RunConfig(max_turns=1)
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Check if response is reasonable
            if "ok" in result.final_output.lower():
                self.health_status.update({
                    "status": "healthy",
                    "last_check": end_time.isoformat(),
                    "response_time": response_time,
                    "error_count": 0
                })
                self.health_status["success_count"] += 1
            else:
                self.health_status.update({
                    "status": "degraded",
                    "last_check": end_time.isoformat(),
                    "response_time": response_time
                })
            
        except Exception as e:
            self.health_status.update({
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "last_error": str(e)
            })
            self.health_status["error_count"] += 1
        
        return self.health_status.copy()
    
    async def continuous_monitoring(self, interval_seconds: int = 300):
        """Continuously monitor agent health"""
        while True:
            await self.health_check()
            print(f"Health check: {self.health_status['status']}")
            await asyncio.sleep(interval_seconds)

# Usage
agent = Agent(name="Production Agent")
health_checker = AgentHealthChecker(agent)

# Start continuous monitoring
asyncio.create_task(health_checker.continuous_monitoring(interval_seconds=60))
```

#### Metrics Collection
```python
import time
from collections import defaultdict
from typing import Dict, List
import json

class AgentMetrics:
    """Collect and track agent performance metrics"""
    
    def __init__(self):
        self.metrics = {
            "request_count": 0,
            "total_response_time": 0,
            "error_count": 0,
            "tool_usage": defaultdict(int),
            "model_usage": defaultdict(int),
            "hourly_requests": defaultdict(int)
        }
        self.request_history: List[Dict] = []
    
    def start_request(self, request_id: str) -> str:
        """Start tracking a request"""
        self.metrics["request_count"] += 1
        current_hour = time.strftime("%Y-%m-%d %H:00")
        self.metrics["hourly_requests"][current_hour] += 1
        return request_id
    
    def end_request(self, request_id: str, response_time: float, 
                   success: bool, model: str = None, tools_used: List[str] = None):
        """End tracking a request"""
        self.metrics["total_response_time"] += response_time
        
        if not success:
            self.metrics["error_count"] += 1
        
        if model:
            self.metrics["model_usage"][model] += 1
        
        if tools_used:
            for tool in tools_used:
                self.metrics["tool_usage"][tool] += 1
        
        # Store request history (keep last 1000)
        self.request_history.append({
            "request_id": request_id,
            "timestamp": time.time(),
            "response_time": response_time,
            "success": success,
            "model": model,
            "tools_used": tools_used or []
        })
        
        if len(self.request_history) > 1000:
            self.request_history.pop(0)
    
    def get_stats(self) -> Dict:
        """Get current metrics"""
        avg_response_time = (
            self.metrics["total_response_time"] / self.metrics["request_count"]
            if self.metrics["request_count"] > 0 else 0
        )
        
        error_rate = (
            self.metrics["error_count"] / self.metrics["request_count"]
            if self.metrics["request_count"] > 0 else 0
        )
        
        return {
            "total_requests": self.metrics["request_count"],
            "average_response_time": round(avg_response_time, 3),
            "error_rate": round(error_rate * 100, 2),
            "top_tools": dict(sorted(self.metrics["tool_usage"].items(), 
                                   key=lambda x: x[1], reverse=True)[:5]),
            "model_distribution": dict(self.metrics["model_usage"]),
            "requests_last_24h": sum(list(self.metrics["hourly_requests"].values())[-24:])
        }
    
    def export_metrics(self, filepath: str):
        """Export metrics to file"""
        with open(filepath, 'w') as f:
            json.dump({
                "metrics": dict(self.metrics),
                "recent_requests": self.request_history[-100:]  # Last 100 requests
            }, f, indent=2)

# Usage with decorator
metrics = AgentMetrics()

async def tracked_agent_request(agent: Agent, user_input: str) -> str:
    """Make agent request with metrics tracking"""
    request_id = f"req_{int(time.time() * 1000)}"
    metrics.start_request(request_id)
    
    start_time = time.time()
    try:
        result = await Runner.run(agent, user_input)
        end_time = time.time()
        
        metrics.end_request(
            request_id=request_id,
            response_time=end_time - start_time,
            success=True,
            model=agent.model,
            tools_used=[tool.__name__ for tool in agent.tools] if agent.tools else None
        )
        
        return result.final_output
        
    except Exception as e:
        end_time = time.time()
        metrics.end_request(
            request_id=request_id,
            response_time=end_time - start_time,
            success=False,
            model=agent.model
        )
        raise e

# Regular metrics reporting
async def report_metrics():
    while True:
        stats = metrics.get_stats()
        print(f"📊 Agent Metrics: {stats}")
        await asyncio.sleep(300)  # Report every 5 minutes
```

### 4. Error Recovery & Resilience

#### Retry Logic
```python
import asyncio
import random
from typing import Callable, Any

class ExponentialBackoff:
    """Exponential backoff retry logic"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def retry(self, func: Callable, *args, **kwargs) -> Any:
        """Retry function with exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    raise e
                
                # Calculate delay with jitter
                delay = min(
                    self.base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self.max_delay
                )
                
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
        
        raise last_exception

# Usage
backoff = ExponentialBackoff(max_retries=3)

async def resilient_agent_call(agent: Agent, user_input: str) -> str:
    """Make agent call with retry logic"""
    
    async def _agent_call():
        return await Runner.run(agent, user_input)
    
    result = await backoff.retry(_agent_call)
    return result.final_output
```

#### Graceful Degradation
```python
class FallbackAgentSystem:
    """System with multiple fallback options"""
    
    def __init__(self):
        # Primary agent (most capable)
        self.primary_agent = Agent(
            name="Primary",
            model="gpt-4o",
            tools=[advanced_tool_1, advanced_tool_2]
        )
        
        # Secondary agent (simpler)
        self.secondary_agent = Agent(
            name="Secondary",
            model="gpt-4o-mini",
            tools=[basic_tool_1]
        )
        
        # Fallback agent (basic responses)
        self.fallback_agent = Agent(
            name="Fallback",
            model="gpt-4o-mini",
            instructions="Provide helpful but basic responses. No external tools available."
        )
    
    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """Process request with fallback chain"""
        
        # Try primary agent
        try:
            result = await Runner.run(self.primary_agent, user_input)
            return {
                "response": result.final_output,
                "agent_used": "primary",
                "success": True
            }
        except Exception as e:
            print(f"Primary agent failed: {e}")
        
        # Try secondary agent
        try:
            result = await Runner.run(self.secondary_agent, user_input)
            return {
                "response": result.final_output,
                "agent_used": "secondary", 
                "success": True,
                "degraded": True
            }
        except Exception as e:
            print(f"Secondary agent failed: {e}")
        
        # Use fallback agent
        try:
            result = await Runner.run(self.fallback_agent, user_input)
            return {
                "response": result.final_output,
                "agent_used": "fallback",
                "success": True,
                "degraded": True,
                "message": "Limited functionality available"
            }
        except Exception as e:
            return {
                "response": "I apologize, but I'm currently experiencing technical difficulties. Please try again later.",
                "agent_used": "none",
                "success": False,
                "error": str(e)
            }

# Usage
fallback_system = FallbackAgentSystem()
result = await fallback_system.process_request("Complex query requiring tools")
```

---

## Final Recommendations

### 1. **Start Simple, Scale Gradually**
- Begin with single-agent patterns
- Add complexity only when needed
- Test thoroughly at each stage

### 2. **Design for Observability**
- Implement comprehensive logging
- Use structured tracing
- Monitor performance metrics
- Plan for debugging from day one

### 3. **Prioritize Safety**
- Implement input/output guardrails
- Validate all user inputs
- Handle sensitive data appropriately
- Plan for graceful failure modes

### 4. **Optimize for Performance**
- Use appropriate models for each task
- Implement caching where beneficial
- Monitor and optimize tool usage
- Consider parallel execution patterns

### 5. **Plan for Production**
- Design for scalability from the start
- Implement proper error handling
- Use configuration management
- Monitor system health continuously

This comprehensive guide should serve as your go-to reference for building production-ready agent systems with the OpenAI Agents SDK. Remember to always test thoroughly and iterate based on real-world usage patterns! 