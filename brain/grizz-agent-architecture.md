# Grizz Chat AI Engine – Architecture Blueprint  
*Last updated: 2023-05-20*

---

## 0. Purpose

> Keep this doc short, opinionated, and forward-looking.  
> We ship an MVP first, but every decision must survive the jump to:
>  * multi-agent logic  
>  * millions of tokens / month  
>  * regulated customers (GDPR, SOC-2)  

---

## 1. Core Principles

| # | Principle | Why we care |
|---|-----------|-------------|
| 1 | **Streaming-first** | Sub-200 ms first token feels "instant". |
| 2 | **Event-driven + durable** | Redis Streams = one truth across pods. |
| 3 | **Future DAG** | Even MVP chat stored as `task → steps` so "planner/actor" slots in later with *zero* schema change. |
| 4 | **Provider-agnostic LLM** | Router swaps OpenAI ↔ Anthropic ↔ Mistral by cost/latency. |
| 5 | **Security-first** | Rate-limit, sandbox, content safety from day 1. |
| 6 | **Cost & usage tracking** | Every completion → `usage_cents` row; fuels billing + anomaly alerts. |
| 7 | **Ops & compliance ready** | OTel traces, nightly DB dumps, GDPR erase, key rotation. |

---

## 2. High-Level Diagram

```
Next.js ──► WebSocket ◄──────────────┐
         (SSE fallback)              │
                                     │
┌──────────┐  Redis Streams          │  Postgres (pgvector)
│ FastAPI  │◄─────────────────┼──────────────────────► storage
│ pods     │                  │
└──────────┘                  │
      ▲ ▲ ▲                   │
      │ │ │     Celery / RQ   │
      │ │ └─────────┐         │
      │ └─────────────┼──────┐│
      │  LLM Router   │Tool  ││
      │ (OpenAI/Anthro)│Sandbox││
      └─────────────────┴───────┴────┘
```

---

## 3. Repo Skeleton (v0)

```
grizz-engine/
├─ web/                         # Next.js
└─ ai-engine/                   
   ├─ app/
   │  ├─ api/                   # chat.py, ws.py, health.py
   │  ├─ core/
   │  │  ├─ config.py           # pydantic Settings, exits if missing vars
   │  │  ├─ events.py           # Redis Stream wrapper
   │  │  ├─ security.py         # HMAC auth + rate-limit
   │  │  ├─ telemetry.py        # OpenTelemetry setup
   │  │  └─ compliance.py       # GDPR utilities
   │  ├─ agents/
   │  │  ├─ base.py
   │  │  └─ chat_agent.py       # only agent in MVP
   │  ├─ llm/
   │  │  ├─ router.py           # cost+latency aware
   │  │  └─ openai_client.py
   │  ├─ tools/
   │  │  ├─ registry.py         # @register_tool
   │  │  └─ sandbox.py          # resource limits
   │  ├─ services/
   │  │  ├─ chat_service.py
   │  │  ├─ memory_service.py
   │  │  └─ moderation.py
   │  └─ db/
   │     ├─ models.py           # tasks, steps, messages, llm_usage, violations
   │     └─ migrations/
   ├─ tests/                    # unit, streaming, load
   └─ Dockerfile
```

---

## 4. Data Model (stable long-term)

```
tasks(id, user_id, status, title, created_at, updated_at)

steps(id, task_id, parent_step_id, type, status,
      provider, prompt_tokens, completion_tokens, usage_cents,
      created_at, updated_at, metadata JSONB)

messages(id, step_id, role, content, token_count,
         created_at, metadata JSONB)

policy_violations(id, user_id, content, categories JSONB,
                  scores JSONB, timestamp, reviewed, action_taken)
```

## 5. MVP (P0) Checklist

| Area | Done when |
|------|-----------|
| Streaming WS | `/ws/chat/{conv}` returns JSON chunks; SSE fallback path. |
| Events | `events.publish('llm_chunk', …)` writes to Redis Stream; WS consumes. |
| ChatAgent | Reads convo context (≤6k tokens), streams deltas, writes steps/messages. |
| Rate limiting | slowapi 5 req/min for anon, 20 for auth. |
| LLM router | OpenAI default; records `usage_cents` row. |
| Content Moderation | OpenAI mod API; blocks severe; logs everything. |
| CI/CD | GitHub Actions: lint → tests → build → push Docker. |

## 6. Phase roadmap (build order)

| Phase | Adds | Refactor risk |
|-------|------|---------------|
| P0 | Chat stream, auth, cost log | baseline |
| P1 | Tool framework + sandbox, smart memory summariser | zero schema change (new step types). |
| P2 | LLM fallback, vector KB, cancel/back-pressure | reuse router & task manager. |
| P3 | Planner + multi-agent, DAG UI, admin dashboard | tasks/steps already support DAG; only code. |
| P4 | Auto-scaling, WS gateway, SOC-2 docs | infra only. |

## 7. Operational Must-haves

**Observability** – TraceID header flows FE→BE; alert on P90 first-token > 3s, 5xx rate > 1%.

**Backups** – Nightly pg_dump to S3; Redis AOF; tested restore.

**Secrets rotation** – Managed store (AWS SecretsManager / 1Password), rotated monthly.

**Compliance** – DELETE `/user/{id}` triggers ComplianceService.delete_user_data.

**Disaster plan** – Runbook: Redis down ⇒ degrade to long-poll w/ DB watch.

## 8. Design Guard-rails

- Never write business logic in WS handler — delegate to services.

- Tools must be pure-async, no global state.

- Any new LLM prompt template hashes stored in prompts table, referenced by step.

- Front-end must reconnect w/ exponential back-off and supply last_event_id for replay.

## 9. Open Questions (parking lot)

- Pick pgvector or Qdrant? Decide by P2.

- Firecracker micro-VM vs Docker sidecars for heavy tools? Test perf at P1.

- Billing model: per-token vs per-minute? Needs product input by P1 end. 