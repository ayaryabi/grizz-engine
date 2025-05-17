# Co-Sight Architecture: A Comprehensive Analysis

## Overview

Co-Sight is a sophisticated multi-agent AI system built around a planner-actor architecture. The system processes user queries by first creating a structured plan with dependencies, then executing each step with specialized agents. A robust API layer connects the system to a web-based frontend for real-time interaction.

## Detailed Folder Structure

```
Co-Sight/
├── .env_template                # Environment configuration template (API keys, model configs)
├── .dockerignore                # Files to exclude from Docker builds
├── .git/                        # Git repository metadata
├── .gitignore                   # Files to exclude from git
├── LICENSE                      # License file (Apache 2.0)
├── MANIFEST.in                  # Package manifest for setuptools
├── README.md                    # Project documentation
├── setup.py                     # Python package setup script
├── __init__.py                  # Root package initialization
├── CoSight.py                   # Core orchestrator class (main execution logic)
├── Dockerfile                   # Container definition for deployment
├── llm.py                       # Initializes different LLM clients (Planner, Actor, Tool, Vision)
├── requirements.txt             # Project dependencies
├── assets/                      # Static assets for the project
├── config/                      # Configuration utilities
│   ├── __init__.py              # Package initialization
│   ├── __pycache__/             # Python cache files
│   ├── config.py                # Main config loader from environment variables
│   └── mcp_server_config.json   # MCP engine configuration
├── logs/                        # Log output directory
├── tools/                       # Utility tools (separate from agent tools)
├── venv/                        # Virtual environment (not in version control)
├── work_space/                  # Runtime working directory
│   └── logs/                    # Execution logs subdirectory
├── app/                         # Main application code
│   ├── __init__.py              # Package initialization
│   ├── __pycache__/             # Python cache files
│   ├── common/                  # Common utilities
│   ├── agent_dispatcher/        # Core agent infrastructure
│   │   ├── __init__.py          # Package initialization
│   │   ├── __pycache__/         # Python cache files
│   │   ├── application/         # Application layer connectors
│   │   ├── domain/              # Domain logic
│   │   │   ├── __init__.py      # Package initialization
│   │   │   ├── __pycache__/     # Python cache files
│   │   │   ├── llm/             # LLM domain logic
│   │   │   └── plan/            # Plan execution domain logic
│   │   │       ├── __init__.py  # Package initialization
│   │   │       ├── __pycache__/ # Python cache files
│   │   │       └── action/      # Action definitions
│   │   │           ├── __init__.py # Package initialization
│   │   │           ├── __pycache__/ # Python cache files
│   │   │           └── skill/    # Skill definitions
│   │   │               ├── __init__.py # Package initialization
│   │   │               ├── __pycache__/ # Python cache files
│   │   │               └── mcp/  # Master Control Program
│   │   │                   ├── __init__.py # Package initialization
│   │   │                   ├── __pycache__/ # Python cache files
│   │   │                   ├── const.py    # Constants for MCP
│   │   │                   ├── engine.py   # MCP engine implementation
│   │   │                   └── server.py   # MCP server implementation
│   │   └── infrastructure/      # Base entity definitions
│   │       ├── __init__.py      # Package initialization
│   │       ├── __pycache__/     # Python cache files
│   │       ├── entity/          # Core entities
│   │       │   ├── __init__.py  # Package initialization
│   │       │   ├── __pycache__/ # Python cache files
│   │       │   └── AgentInstance.py # Agent instance definition
│   │       └── util/            # Infrastructure utilities
│   └── cosight/                 # Co-Sight specific implementations
│       ├── __init__.py          # Package initialization
│       ├── __pycache__/         # Python cache files
│       ├── HanSerif.ttf         # Font file for visualizations
│       ├── requirements.txt     # Module-specific dependencies
│       ├── agent/               # Agent implementations
│       │   ├── __init__.py      # Package initialization
│       │   ├── __pycache__/     # Python cache files
│       │   ├── base/            # BaseAgent framework
│       │   │   ├── __init__.py  # Package initialization
│       │   │   ├── __pycache__/ # Python cache files
│       │   │   ├── base_agent.py # Common agent functionality
│       │   │   ├── common_skill.py # Common agent skills
│       │   │   └── skill_to_tool.py # Converts skills to tools
│       │   ├── planner/         # Planning agent
│       │   │   ├── __init__.py  # Package initialization
│       │   │   ├── __pycache__/ # Python cache files
│       │   │   ├── instance/    # Planner instance definitions
│       │   │   │   ├── __init__.py # Package initialization
│       │   │   │   ├── __pycache__/ # Python cache files
│       │   │   │   └── planner_agent_instance.py # Planner instance factory
│       │   │   ├── prompt/      # Planner prompts
│       │   │   └── task_plannr_agent.py # Plan creation logic
│       │   └── actor/           # Actor agent for executing steps
│       │       ├── __init__.py  # Package initialization
│       │       ├── __pycache__/ # Python cache files
│       │       ├── instance/    # Actor instance definitions 
│       │       │   ├── __init__.py # Package initialization
│       │       │   ├── __pycache__/ # Python cache files
│       │       │   └── actor_agent_instance.py # Actor instance factory
│       │       ├── prompt/      # Actor prompts
│       │       └── task_actor_agent.py # Step execution logic
│       ├── llm/                 # LLM integration wrappers
│       │   ├── __init__.py      # Package initialization
│       │   ├── __pycache__/     # Python cache files
│       │   └── chat_llm.py      # Common LLM interface
│       ├── record/              # Execution recording utilities
│       ├── task/                # Task management
│       │   ├── __init__.py      # Package initialization
│       │   ├── __pycache__/     # Python cache files
│       │   ├── plan_report_manager.py # Event-based update mechanism
│       │   ├── task_manager.py  # Manages active tasks/plans
│       │   ├── time_record_util.py # Performance tracking utilities
│       │   └── todolist.py      # Plan implementation with DAG structure
│       └── tool/                # Tool implementations
│           ├── __init__.py      # Package initialization
│           ├── __pycache__/     # Python cache files
│           ├── act_toolkit.py   # Action tools for steps
│           ├── audio_toolkit.py # Audio processing tools
│           ├── code_toolkit.py  # Code execution tools
│           ├── deep_search/     # Advanced search capabilities
│           ├── document_processing_toolkit.py # Document handling tools
│           ├── excel_toolkit.py # Excel file operations
│           ├── file_download_toolkit.py # File download utilities
│           ├── file_toolkit.py  # File operations
│           ├── google_api_key.py # Google API integration
│           ├── google_search_util.py # Google search tools
│           ├── html_visualization_toolkit.py # HTML generation tools
│           ├── image_analysis_toolkit.py # Image processing tools
│           ├── interpreters/    # Code interpretation tools
│           ├── plan_toolkit.py  # Plan manipulation tools
│           ├── scrape_website_toolkit.py # Web scraping tools
│           ├── search_toolkit.py # Search capabilities
│           ├── search_util.py   # Search utilities
│           ├── shell_toolkit.py # Shell command execution
│           ├── simhei.ttf       # Font file for visualizations
│           ├── terminate_toolkit.py # Agent termination tools
│           ├── video_analysis_toolkit.py # Video processing tools
│           └── web_util.py      # Web utilities
├── cosight_server/              # API server
│   ├── cosight_server/          # Internal server implementation
│   ├── deep_research/           # Main API application
│   │   ├── __init__.py          # Package initialization
│   │   ├── __pycache__/         # Python cache files
│   │   ├── common/              # Common utilities for API
│   │   ├── entity.py            # Entity definitions for API
│   │   ├── main.py              # FastAPI app setup
│   │   ├── routers/             # API endpoint definitions
│   │   │   ├── __init__.py      # Package initialization
│   │   │   ├── __pycache__/     # Python cache files
│   │   │   ├── chat_manager.py  # Chat API endpoints
│   │   │   ├── common.py        # Common API utilities
│   │   │   ├── feedback.py      # Feedback API endpoints
│   │   │   ├── search.py        # Search endpoint (main entry point)
│   │   │   ├── user_manager.py  # User management endpoints
│   │   │   └── websocket_manager.py # WebSocket management
│   │   ├── service.py           # Service implementations
│   │   └── services/            # Backend services
│   ├── manus_server/            # Secondary server component
│   ├── sdk/                     # Common SDK for server components
│   │   ├── __init__.py          # Package initialization
│   │   ├── __pycache__/         # Python cache files
│   │   ├── common/              # Common utilities
│   │   │   ├── __init__.py      # Package initialization
│   │   │   ├── __pycache__/     # Python cache files
│   │   │   ├── SourceHanSansCN-Normal.otf # Font file
│   │   │   ├── api_result.py    # API result formatting
│   │   │   ├── cache.py         # Caching utilities
│   │   │   ├── cipher_utils.py  # Encryption utilities
│   │   │   ├── config.py        # SDK configuration
│   │   │   ├── logger_util.py   # Logging utilities
│   │   │   ├── singleton.py     # Singleton pattern implementation
│   │   │   └── utils.py         # General utilities
│   │   ├── entities/            # Entity definitions
│   │   └── services/            # Service implementations
│   ├── upload_files/            # File upload storage
│   ├── web/                     # Web server static files
│   └── work_space/              # Server workspace
└── cosight_ui/                  # Frontend UI code
```

## Agent Flow Architecture

### 1. Main Components

1. **CoSight Orchestrator (`CoSight.py`)**
   - The central coordinator that manages the entire workflow
   - Initializes agents with appropriate LLMs
   - Manages plan execution and parallel step processing
   - Uses ThreadPoolExecutor for concurrent step execution
   - Controls the entire agent lifecycle from planning to completion

2. **LLM Manager (`llm.py`)**
   - Creates and configures specialized LLM instances for different roles:
     - `llm_for_plan`: Optimized for planning (might use more tokens/higher reasoning)
     - `llm_for_act`: Optimized for execution (handles tool usage)
     - `llm_for_tool`: Used for tool-specific processing
     - `llm_for_vision`: Handles multimodal inputs (images, etc.)
   - Sets up custom httpx clients with appropriate headers and proxies
   - Provides consistent interface for all LLM interactions

3. **Plan Model (`app/cosight/task/todolist.py`)**
   - Represents tasks as a DAG (Directed Acyclic Graph)
   - Tracks step dependencies, status, notes, and artifacts
   - Provides methods to find "ready" steps (all dependencies completed)
   - Handles workspace path management for generated files
   - Manages completion state and progress tracking

4. **Agents**
   - **BaseAgent (`app/cosight/agent/base/base_agent.py`)**
     - Provides common agent loop functionality
     - Handles tool execution and conversation management
     - Implements retry logic and error handling
     - Supports both regular and MCP tool execution
   
   - **TaskPlannerAgent (`app/cosight/agent/planner/task_plannr_agent.py`)**
     - Specialized agent for creating structured plans
     - Defines steps and dependencies based on user queries
     - Can re-plan if execution gets blocked
     - Creates the initial plan structure and handles finalization
   
   - **TaskActorAgent (`app/cosight/agent/actor/task_actor_agent.py`)**
     - Executes individual plan steps
     - Selects and uses appropriate tools
     - Records execution results and artifacts
     - Updates step status in the plan

5. **Tool Framework**
   - Rich collection of tools for different tasks
   - Consistent interface via the `skill_to_tool` conversion
   - Categories include:
     - File operations (`file_toolkit.py`)
     - Web search and retrieval (`search_toolkit.py`)
     - Code execution (`code_toolkit.py`)
     - Document processing (`document_processing_toolkit.py`)
     - Media analysis - image, audio, video (`image_analysis_toolkit.py`, `audio_toolkit.py`, `video_analysis_toolkit.py`)

6. **MCP Engine (`app/agent_dispatcher/domain/plan/action/skill/mcp/engine.py`)**
   - Master Control Program for extensible tool execution
   - Handles dynamic loading and invocation of tools
   - Provides isolation for tool execution
   - Coordinates with the BaseAgent for tool management

### 2. Event System

The system uses an event-driven architecture for real-time updates:

- `plan_report_event_manager` (`app/cosight/task/plan_report_manager.py`)
  - Provides publish-subscribe mechanism for plan updates
  - Events include: plan_created, plan_updated, plan_process, plan_result
  - Subscribers can receive real-time updates as plans progress
  - Used by the API layer to stream updates to the frontend

### 3. Execution Flow

1. **Plan Creation**:
   ```
   User Query → CoSight → TaskPlannerAgent → Plan Object
   ```
   
   - The user submits a query via the API
   - CoSight initializes a TaskPlannerAgent with planner LLM
   - The agent creates a structured plan with steps and dependencies
   - The plan is stored in the task manager and events are published

2. **Step Execution**:
   ```
   Plan → get_ready_steps() → TaskActorAgent → Tool Execution → Step Update
   ```
   
   - CoSight gets "ready" steps (all dependencies satisfied)
   - For each ready step, a TaskActorAgent is created
   - Agents can run in parallel (ThreadPoolExecutor)
   - Each agent executes its step and updates the plan
   - Events are published for real-time UI updates

3. **Plan Refinement**:
   ```
   Execution Results → TaskPlannerAgent → Plan Updates
   ```
   
   - If steps get blocked, the planner can revise the plan
   - New steps can be added or dependencies modified
   - The process continues until all steps complete or reach finality

## FastAPI and UI Connection

### API Layer (`cosight_server/deep_research/`)

1. **Main FastAPI App** (`main.py`)
   - Sets up the FastAPI application
   - Configures CORS, middleware, static files
   - Includes routers for different endpoints
   - Handles startup/shutdown events

2. **Search Router** (`routers/search.py`)
   - Main entry point for user queries
   - `/deep-research/search` endpoint receives search requests
   - Creates a CoSight instance and manages its execution
   - Streams results back to the client using `StreamingResponse`
   - Sets up event subscribers to capture plan updates

3. **WebSocket Manager** (`routers/websocket_manager.py`)
   - Maintains real-time connections with clients
   - Broadcasts plan updates as they occur
   - Provides connection handling (connect/disconnect/send)
   - Manages WebSocket lifecycle and error handling

### Real-Time Update Flow

```
CoSight → Event Publication → Queue → WebSocket/StreamingResponse → Client
```

1. **Event Generation**:
   - CoSight updates plan status during execution
   - Events are published to `plan_report_event_manager`
   - Different event types (plan_created, plan_updated, etc.) represent different stages

2. **Queue Processing**:
   - Events are pushed to an async queue (`plan_queue`)
   - AsyncIO event loop processes the queue
   - Serialization happens in the queue processing stage

3. **Data Streaming**:
   - Two methods for sending updates:
     - HTTP Streaming: Using FastAPI's `StreamingResponse`
     - WebSockets: Real-time bidirectional communication
   - Updates are formatted as JSON for client consumption

4. **Client Reception**:
   - UI subscribes to WebSocket updates
   - Updates are processed and displayed in real-time
   - Interface shows plan progress, step statuses, and results

### Request-Response Cycle

1. Client sends a search query to `/deep-research/search`
2. Server starts a background thread running CoSight
3. CoSight begins executing and publishes events
4. Events are queued and streamed back to the client
5. Client receives and displays the results in real-time
6. Each step execution generates updates visible to the user
7. Final result is streamed when all steps complete

## Key Design Patterns

1. **Multi-Agent System**
   - Specialized agents for different phases (planning, execution)
   - Common base agent functionality with specialization
   - Tool-based extension of agent capabilities

2. **Dependency Injection**
   - LLMs and configurations are injected into agents
   - Allows for flexibility in model selection and configuration
   - Different models can be used for different components

3. **Event-Driven Architecture**
   - Real-time updates via event publication
   - Loosely coupled components communicate through events
   - Allows for asynchronous processing and feedback

4. **Directed Acyclic Graph (DAG) Task Model**
   - Tasks represented as steps with dependencies
   - Enables parallel execution of independent steps
   - Provides clear visualization of task progress

5. **Skill-to-Tool Conversion**
   - Common interface for capabilities as "tools"
   - Standardized format for LLM tool usage
   - Makes it easy to add new tools to the system

6. **Factory Pattern**
   - Agent instances are created via factory methods
   - Centralizes instance creation and configuration
   - Simplifies the creation of complex objects

## Security and Configuration

1. **Environment-Based Configuration**
   - All sensitive information stored in environment variables
   - `.env_template` provides structure for required variables
   - Multiple configuration options for different LLM roles

2. **Model Flexibility**
   - Different LLMs can be used for different components
   - Fallback to default configurations if specifics not provided
   - Configurable parameters (temperature, max_tokens, etc.)

3. **Workspace Isolation**
   - Each execution run uses a timestamped workspace
   - Prevents conflicts between concurrent executions
   - Preserves execution artifacts for review

## Conclusion

Co-Sight represents a sophisticated architecture that combines multi-agent AI with modern web technologies. The system's strength lies in its structured approach to task planning and execution, with real-time feedback to users. The separation of planning and execution agents, coupled with a rich tool ecosystem, allows it to tackle complex tasks with a methodical approach.

The event-driven nature of the system enables responsive UI updates, while the FastAPI backend provides a robust and scalable foundation. The clean separation of concerns across different layers (infrastructure, domain, application, API) makes the codebase maintainable and extensible. 