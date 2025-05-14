# Simplified Co‑Sight Agent Rebuild Plan **v2**

---

## Phase 0 – Foundation & Setup

|  Step  |  Deliverable                                                                       |
| ------ | ---------------------------------------------------------------------------------- |
| `0.1`  |  Project skeleton (`mini_agent/`, `tests/`, `.env`, `shared/`)                     |
| `0.2`  |  Typed **LLM client** wrapper (OpenAI/Anthropic)                                   |
| `0.3`  |  `Plan`, `Step`, `ToolCall`, `ToolResult` Pydantic models (in `shared/schemas.py`) |
| `0.4`  |  Cost‑tracking & logging middleware (basic Python logging initially)                 |
| `0.5`  |  Add basic web server dependencies (`fastapi`, `uvicorn`)                          |
| `0.6`  |  **Setup LangSmith Environment** (Env vars, optional SDK install for basic tracing) |

---

## Phase 1 – Planner Agent

|  Step  |  Deliverable                                                                       |
| ------ | ---------------------------------------------------------------------------------- |
| `1.1`  |  `planner_system_prompt` & `planner_create_plan_prompt`                            |
| `1.2`  |  `PlannerAgent.generate_plan(query)` returns Plan object                           |
| `1.3`  |  Prompt versioning (hash + timestamp in each call)                                 |
| `1.4`  |  Unit tests → expected Plan object structure                                       |
| `1.5`  |  **Basic API endpoint** (`api.py`) that takes query, runs `1.2`, returns Plan JSON |

---

## Phase 2 – BaseAgent & Tool Registry

|  Step  |  Deliverable                                                                      |
| ------ | ----------------------------------------------------------------------------------|
| `2.1`  |  `BaseAgent` loop with guard‑railed JSON parsing & auto‑retry                     |
| `2.2`  |  Global **Tool Registry** (`@tool` decorator)                                     |
| `2.3`  |  First internal tool `record_plan(plan: Plan)` updating state object              |
| `2.4`  |  Streaming support (partial deltas)                                               |

---

## Phase 3 – Actor Agent & Executable Tools

|  Step  |  Deliverable                                                                        |
| ------ | ----------------------------------------------------------------------------------  |
| `3.1`  |  `actor_system_prompt` & `actor_execute_step_prompt`                                |
| `3.2`  |  Worker tools: `save_text`, `execute_code` (sandboxed)                              |
| `3.3`  |  `ActorAgent.execute_step(step: Step)` with automatic tool execution & state update |
| `3.4`  |  Vision / Audio / Web helpers stubbed via separate Worker classes                   |

---

## Phase 4 – Orchestrator & Facade

|  Step  |  Deliverable                                                                                    |
| ------ | ---------------------------------------------------------------------------------------------- |
| `4.1`  |  `MiniCoSight` orchestrator linking Planner → Actor, managing `Plan` state (in-memory)initially|
| `4.2`  |  `Plan.get_ready_steps()` logic for DAG execution integrated into orchestrator                  |
| `4.3`  |  **SubAgentFacade class** exposing minimal external contract (e.g., `run_task(query) -> final_result`) |
| `4.4`  |  ASCII / Mermaid plan visualiser                                                               |
| `4.5`  |  Embedded evaluation harness (YAML test cases)                                                 |
| `4.6`  |  **Integrate Facade (`4.3`) into API endpoint (`1.5`)**, potentially adding streaming          |
| `4.7`  |  *(Consider state persistence options beyond in-memory for future scalability)*                |

---

## Phase 5 – Enhancements

*   Add real web‑search, Tavily, browser‑use workers.
*   Parallel step execution via `asyncio.gather`.
*   Vector‑store memory + RetrievalTool.
*   Implement chosen state persistence (DB/Redis/etc.) if needed.
*   Swap orchestration to **LangGraph** once loops/branches grow.
*   Develop a simple HTML/JS frontend interacting with the API.

---

## Golden Nuggets 🍯  (to save future refactors)

|  #  |  Nugget                      |  Benefit                         |
| --- | ---------------------------- | -------------------------------- |
| 1   | Typed data‑models everywhere | Auto‑validation & easier tests   |
| 2   | Central Tool Registry        | One‑liner tool onboarding        |
| 3   | Cost/token logging           | Catch runaway loops early        |
| 4   | Streaming support            | Better UX; long‑running tools OK |
| 5   | Guard‑rail auto‑retry        | Eliminate JSON‑format crashes    |
| 6   | Plan visualiser              | Instant debugging insight        |
| 7   | Built‑in eval harness        | Regression safety net            |
| 8   | CPU/RAM sandbox limits       | Protect host machine             |
| 9   | Prompt hashing               | Reproducibility across runs      |
| 10  | Single `config.toml`         | Flip models/keys in one file     |

---

### Minimal Example `Plan` Model

```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

class Status(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed   = "completed"
    blocked     = "blocked"

class Step(BaseModel):
    index: int
    description: str
    status: Status = Status.not_started
    deps: List[int] = Field(default_factory=list)

class Plan(BaseModel):
    title: str
    steps: List[Step]

    def get_ready_steps(self):
        # Basic implementation - assumes steps are processed in order
        # A real implementation would check deps based on completed status
        # This is just for the model example
        ready = []
        for step in self.steps:
            if step.status == Status.not_started:
                 # Check if all dependencies are met
                 all_deps_met = True
                 for dep_index in step.deps:
                     # Ensure dependency index is valid
                     if dep_index < 0 or dep_index >= len(self.steps):
                         # Handle invalid dependency index, maybe log an error or raise exception
                         # For simplicity, we'll assume valid indices for this example
                         continue 
                     if self.steps[dep_index].status != Status.completed:
                         all_deps_met = False
                         break
                 if all_deps_met:
                     ready.append(step)
            # Simplified: Return the first ready step for linear execution initially
            # A real scheduler might return all ready steps for parallel execution
            if ready: 
                # This example only returns the first ready step
                # In a real scenario, might return list: ready
                # return ready
                return ready[0:1] # Return as list containing one item for simplicity now
                
        return [] # No ready steps


```

> **Next milestone:** implement Phase 0 and run `pytest tests/phase0_foundation.py` to lock behavior.

---

## Appendix: Co-Sight Original Architecture (High-Level Summary)

This section summarizes the perceived high-level architecture of the original Co-Sight project for reference.

```
Co-Sight/
├── .env / .env_template       # Configuration (API Keys, Model Names)
├── config/                     # Python helpers to load .env config
├── llm.py                      # Initializes specific LLM clients (Planner, Actor, etc.)
├── CoSight.py                  # Core Orchestrator class (initiates plan, loops steps)
├── cosight_server/             # Backend FastAPI Web Server
│   ├── sdk/                    # Implied: Common SDK/Utilities (Config, Logging?)
│   └── deep_research/
│       ├── main.py             # FastAPI app setup, middleware, static files, uses SDK
│       └── routers/            # API endpoint definitions
│           ├── search.py       # Handles '/search' endpoint, triggers agent, streams results
│           ├── websocket_manager.py # Handles real-time UI updates
│           └── ...             # Other routers (user, common, etc.)
├── app/
│   ├── agent_dispatcher/       # Core Agent Infrastructure/Framework?
│   │   ├── infrastructure/     # Defines Entities like AgentInstance?
│   │   └── domain/             # Defines Domain Logic like MCP Engine?
│   └── cosight/
│       ├── agent/              # Co-Sight Specific Agent Logic
│       │   ├── base/           # BaseAgent class (Uses AgentInstance, runs LLM/tool loop)
│       │   ├── planner/        # Planner-specific logic, prompts, instance defs
│       │   └── actor/          # Actor-specific logic, prompts, instance defs
│       ├── tool/               # Implementations of specific tools (Search, File I/O, Web, etc.)
│       ├── task/               # Task state management (Plan object, events)
│       └── llm/                # Wrapper around LLM clients (ChatLLM)
├── cosight_ui/ (or web/)       # Frontend UI Code (HTML, JS, CSS) - Assumed location
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Containerization setup
├── work_space/                 # Runtime directory for logs, intermediate files, results
└── ...                         # Other supporting files (README, LICENSE, setup.py)
```

**Key Architectural Patterns:**

*   **Layered Structure:** Appears to have distinct layers: Infrastructure (`agent_dispatcher`, `sdk`), Application Logic (`app/cosight/`), Server (`cosight_server`), and potentially UI (`cosight_ui`).
*   **Separation of Concerns:** Clear separation between Web Server (FastAPI), Core Orchestration (`CoSight.py`), Specific Agent Logic (`app/cosight/agent/`), Tools (`app/cosight/tool/`), and underlying Infrastructure (`agent_dispatcher`).
*   **Multi-Agent Structure:** Distinct Planner and Actor agents with specialized roles and prompts, likely built upon the `AgentInstance` definition from `agent_dispatcher`.
*   **Centralized State:** A `Plan` object likely manages the task state.
*   **Event-Driven Updates:** Uses events (`plan_report_event_manager`) and queues for communication, particularly for streaming updates to the UI via WebSockets.
*   **Configuration Driven:** Relies heavily on `.env` for configuring models and keys, likely accessed via helpers in `config/` and the `sdk`.
*   **Custom Orchestration:** The primary agent execution loop appears to be custom-built within `CoSight.py` and `BaseAgent.py`.
