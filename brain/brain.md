# Grizz Engine v1 – Technical & Product Spec

---
## 1 Purpose & Vision
Grizz Engine is the **AI brain‑service** that powers the Grizz writing companion. It turns chat messages into structured knowledge (Bytes), retrieves that knowledge on demand, and can run multi‑step **Quests** that auto‑generate new Bytes. Everything lives behind a single FastAPI micro‑service so the UI and future clients remain thin.

---
## 2 High‑Level Architecture
```
Browser  ──►  Next.js /api/chat
                  │ (SSE proxy)
                  ▼
        FastAPI ("grizz‑engine")
                  │    ── OpenAI Agents SDK
                  ▼
    Postgres + pgvector (Supabase)
```
* **UI (Next.js 14)** – Chat pane, Bytes Hub, Quest launcher.
* **Grizz Engine (FastAPI)** – Hosts the Manager agent, tools, and sub‑agents.
* **Database** – `users`, `bytes`, `entities`, `byte_entities`, `user_facts` (+ pgvector column on `bytes`).
* **Docker Compose** – spins the trio (`ui`, `engine`, `db`) locally & in CI.

---
## 3 Prompt Stack (assembled per request)
| Order | File | Size ≈ tokens | Note |
|-------|------|---------------|------|
| 1 | `CORE_SYSTEM.md` | ≈400 | Persona, tone, hard rules. |
| 2 | `AGENT_LOOP.md` | ≈250 | 6‑step deterministic loop (Analyze → Tool → …). |
| 3 | `TOOLS.json` (list only) | ≈150 | Name + signature for each tool. |
| 4 | `GUARDRAILS.md` | ≈120 | Moderation, retry, escalation. |
| 5 | (optional) `SUB_AGENT_PROMPT_xyz` | ≈200 | Outliner, Drafter, etc. |
| 6 | **Dynamic Context** | ≤1 000 | Last 6 turns, top‑K Byte snippets, ≤5 user_facts. |
Total worst‑case ≈ 2 100 tokens → well under GPT‑4o’s window.

---
## 4 Core Tools (JSON Function Calls)
| Tool | Args | Action |
|------|------|--------|
| **ByteCreate** | `title, content_md, tags?` | Saves Byte, runs entity extraction, inserts links. |
| **ByteSearch** | `query, filter_tags?, limit?` | Vector + tag search → returns Bytes list. |
| **QuestGenerate** | `topic` | Launches Outliner → Drafter, then ByteCreate. |
| **MessageNotify** | `text` | Progress pings to UI. |
| **MessageAsk** | `text` | Escalation / human‑handoff.

*Tools live as Python functions; only their schema appears in the prompt.*

---
## 5 Entity Model v1 (Lean 9 Buckets)
`type ∈ {person, organization, project, event, location, thing, topic, process, time_period}`

* Extra nuance via `kind` field (e.g. `thing.kind = "tool"`).
* Table **`entities`**: `id, user_id NULL→public, type, name, kind?, props JSONB, embedding`.
* Table **`entity_links`**: `src_id, dst_id, rel_type, props JSONB`.
* **Promotion rule**: if ≥2 distinct users link the same name+type → set `user_id = NULL` (public).

---
## 6 Quest Pipeline
1. **Manager** receives `/quest topic` → decides tool `QuestGenerate`.
2. **Outliner Sub‑Agent** – builds bullet structure, grounded by quick WebSearch anchors.
3. **Drafter Sub‑Agent** – fleshes prose + citations.
4. *(v1.1)* Illustrator – optional image generation.
5. **Assembler** – calls `ByteCreate` with `quest_origin:true`, returns link.

Progress updates stream via `MessageNotify` (“Outlining ✅ – drafting … ”).

---
## 7 Guardrails
* **OpenAI Moderation** on user input → block if violent, sexual, disallowed.
* **JSON‑retry wrapper** – auto‑repair malformed tool calls up to 2×.
* **Escalation** – on third failure or risky action → `MessageAsk` to summon human.

---
## 8 Development Roadmap (Week‑by‑Week)
| Week | Deliverables |
|------|--------------|
| 1 | Repo + compose skeleton, empty FastAPI stub, DB schema. |
| 2 | Implement `ByteCreate`, `ByteSearch`; write unit tests (curl). |
| 3 | Add guardrails + `user_facts`; integrate pgvector. |
| 4 | Build `QuestGenerate` (Outliner + Drafter); progress SSE. |
| 5 | Next.js chat UI wired to `/chat`; streaming works. |
| 6 | Bytes Hub UI (grid, filter, shuffle) + basic auth. |
| 7 | Metrics (p95, cost) + Sentry; private beta. |

---
## 9 KPIs & SLOs
| Metric | Target |
|--------|--------|
| p95 latency | ≤ 3 s end‑to‑end |
| JSON failure rate | < 2 % (auto‑retry covers rest) |
| Guardrail false positive | < 5 % |
| Memory recall P@5 | ≥ 0.8 |

---
## 10 Future Extensions
* **Domain Packs** for health, legal, bio‑chem entities.
* **Slack Bot Mirror** using same engine.
* **Voice capture → Byte** on mobile.
* **Graph‑RAG** retrieval once entity links mature.
* **Rich editor / inline autocomplete** (move back into UI after v1).

*End of spec – commit & iterate.*

