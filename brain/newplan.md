# GRIZz — MVP Technical & Product Specification

## 1. Mission & Product North‑Star

Build a character‑driven command‑center that feels like a personal Jarvis, starting with:

1. **Conversational hub** (single rolling chat that resets daily, voice & text input, GPT‑4o personality "Grizz Barrington").
2. **Long‑term Memory** (“Bytes”) with lightning retrieval.

Everything else (entities, automations, integrations) is add‑on after solid v1 traction.

---

## 2. Primary Personas for v1 Launch

| Persona                               | Pain Today                                                  | Why GRIZz resonates                                          | Early‑adoption channel                   |
| ------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------- |
| Indie‑hackers / solo builders (18‑35) | Dozens of ChatGPT threads, scattered research, context lost | Daily‑reset chat, quick byte saving, programmable memory     | X / Product Hunt / Indie Hackers forum   |
| Gen‑Z college students (18‑24)        | Need quick study help, organise sources, write drafts       | Fun bear personality, low \$10–20, voice memos, byte tagging | Campus groups, TikTok, student discounts |

v1 leans indie‑hackers for sharper feedback & willingness to pay \$20.

---

## 3. Feature Scope — MVP Freeze

### 3.1 Conversational Core

* **Chat panel** (command center)

  * Text input + ⌘+Enter to expand full‑screen editor
  * Voice memo → Whisper transcribe
  * Personality prompt injected on every request
* **Daily reset** (UTC‑offset per user)

  * Archive previous messages ➜ `messages` table
  * Trigger `daily_summary` background job

### 3.2 Memory / Bytes

* Byte types: `doc`, `pdf`, `url`, `note`, `video`, `audio`
* Auto‑tag via small system prompt
* Store raw + json metadata + SHA‑256 dedupe hash
* pgvector embedding (OpenAI Ada‑002)
* Search tier:

  1. Keyword + tag filter
  2. Semantic vector search
* **Byte chat split‑view**

  * `chat?id=<byte_id>` renders 2‑pane (byte preview + thread)

### 3.3 Background Jobs

| Job             | Schedule     | Action                                        |
| --------------- | ------------ | --------------------------------------------- |
| `daily_summary` | 00:05 local  | Summarise yesterday → save to `daily_summary` |
| `embed_byte`    | onByteUpload | Generate embedding, tags, dedupe check        |

### 3.4 UX Polish (delighters)

* Animated "Grizz is thinking…" states
* Light / Dark toggle

---

## 4. System Architecture

```mermaid
graph LR
A[Next.js 14 App] -- RPC --> B[FastAPI Service]
A -- Supabase JS --> C[(Postgres + pgvector)]
A -- Storage --> D[S3 (Supabase)]
B -- Celery/Redis --> E[Workers]
B --> C
E --> C
C --> B
```

### 4.1 Front‑end (apps/web)

* React + Next.js App Router
* shadcn/ui + Tailwind (atomic design)
* Clerk for auth wrapper around Supabase (optional)
* TanStack Query for data

### 4.2 Back‑end (apps/api)

* FastAPI + Pydantic
* OpenAI SDK wrapper
* Celery + Redis (docker compose) for jobs
* Stripe for payments (supabase extension)

### 4.3 Database (db/schema.sql)

```sql
users(id, email, stripe_id, tz)
messages(id, user_id, role, content, created_at)
bytes(id, user_id, title, type, tags, url, hash, pg_embedding, created_at)
byte_threads(id, user_id, byte_id)
subscriptions(id, user_id, tier, status)
daily_summary(id, user_id, date, content)
```

---

## 5. Monorepo Structure

```
/ (pnpm workspace)
│
├─ apps/
│   ├─ web/           # Next.js 14 (+ shadcn/ui)
│   └─ api/           # FastAPI, Celery, workers
│
├─ packages/
│   ├─ ui/            # atomic components, themes
│   ├─ prompts/       # system & task prompts (yml)
│   ├─ lib/           # shared TS/Py utils
│   └─ types/         # Zod & Pydantic schemas
│
├─ infra/
│   ├─ docker/
│   └─ terraform/     # later
│
├─ db/
│   ├─ migrations/
│   └─ schema.sql
└─ README.md
```

---

## 6. Prompt Catalogue (packages/prompts)

* `system/personality.md` – Bear persona
* `system/tagging.md` – Return JSON {title, tags\[]}
* `system/daily_summary.md` – 3‑bullet digest

---

## 7. API Endpoints (OpenAPI)

| Method | Path    | Purpose            |
| ------ | ------- | ------------------ |
| POST   | /chat   | stream reply       |
| POST   | /bytes  | upload / save      |
| GET    | /bytes  | list & filter      |
| GET    | /search | keyword + semantic |

---

## 8. Roll‑out Plan

1. **Week 0:** Code scaffolding, supabase, auth.
2. **Week 1:** Chat panel, personas, OpenAI streaming.
3. **Week 2:** Byte upload + search + embeddings.
4. **Week 3:** Daily summary cron, polish UI, billing \$20.
5. **Week 4:** Private alpha (50 indie hackers) ➔ collect metrics.
6. Launch on Product Hunt once retention D1 > 40%.

---

## 9. Risks & Mitigations

| Risk             | Mitigation                                             |
| ---------------- | ------------------------------------------------------ |
| Feature creep    | Strict MVP freeze list (above). Any new idea → Icebox. |
| LLM cost blow‑up | Token throttling, fall‑back to GPT‑3.5 for heavy jobs. |
| Duplicate bytes  | hash + user\_id UNIQUE constraint.                     |

---

## 10. Next Steps

* Lock MVP spec ✓ (this doc)
* Convert to GitHub issues (project board)
* Kick‑off sprint #1 (7 days)
* Prep teaser site + early waitlist

---

**GRIZz is now scoped. Build fast, ship, then grow!**
