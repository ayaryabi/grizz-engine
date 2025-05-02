# Grizz v0.1 — Implementation Timeline

> **Trim-to-win timeline** - Progressive implementation with working prod at every step

## Development Sequence

1. **Auth + RLS (day 0)**
   - Magic-link on Supabase
   - One universal RLS rule: user_id = auth.uid()

2. **Schema migrations (same sprint)**
   - Run supabase db push with all required tables
   - Empty columns are fine; structure must exist before code hits it

3. **Hello-world chat loop**
   - Tiny Next page → FastAPI → GPT → stream back
   - No tools, no DB writes yet—just prove latency + auth headers work

4. **Tool layer + ByteCreate**
   - Add JSON tool specs
   - ByteCreate inserts into bytes, queues Redis job
   - Front-end shows "Saved!" with real ID

5. **Workers online**
   - Redis + RQ (or Bun) on Fly → do OCR, property extract, entity pipeline, embeddings

6. **ByteSearch + other tools**
   - Now you've got embeddings in pgvector—wire the search tool and close the loop

7. **Quest & fancy stuff**
   - Once CRUD + search feel solid, layer planner agents, UI polish, etc.

## Why This Order?

- Migrations before code = zero phantom column errors
- Minimal chat loop early = catch CORS / JWT / streaming issues before the stack gets busy
- Workers right after first DB write = no half-baked Bytes hanging around

Ship each slice; prod stays green the whole way.

---

# Grizz Data & Tool Reference (v0.1)

> **Purpose** – living cheat‑sheet you can keep open in Cursor while coding.  Update here **before** touching migrations or tool specs.
>
> **Legend**  
> • `PK` = Primary Key (uuid)  
> • `FK` = Foreign Key (uuid)  
> • TIMESTAMPTZ columns are implicit (`created_at`, `updated_at`).

---

## 1  Database Schema (plain‑English bullets)

- **users / profiles**  
  • `users` comes from Supabase Auth.  
  • `profiles` has `user_id (PK & FK)`, display name, avatar url, plan tier.

- **bytes**  
  • `id (PK)`  
  • `user_id (FK)`  
  • `parent_id` – nullable self‑reference for folders / hierarchy  
  • `item_type` – `'note' | 'document' | 'recipe' | 'paystub' | …`  
  • `title`  
  • `content` – TipTap JSON or plain MD  
  • `properties` – JSONB, validated per *item_type*  
  • `embedding` – `vector(1536)` (pgvector)

- **entities**  
  • `id (PK)`  
  • `user_id (FK)`  
  • `entity_type` – `'person' | 'organization' | 'project' | …`  
  • `name`  
  • `properties` – JSONB (e.g., roles, website)  
  • `embedding` – optional vector for future cross‑user graph.

- **byte_entity_links** (Byte → Entity)  
  • `id (PK)`  
  • `byte_id (FK)`  
  • `entity_id (FK)`  
  • `relationship_type` – usually `'about'`.

- **byte_links** (Byte ↔ Byte)  
  • `id (PK)`  
  • `source_byte_id (FK)`  
  • `target_byte_id (FK)`  
  • `link_type` – `'panel_reference' | 'inline_reference' | 'ai_suggested'`  
  • `position` – int for ordered panels  
  • `properties` – JSONB for extra.

- **entity_entity_links** (Graph edges – start empty)  
  • `id (PK)`  
  • `source_id (FK → entities)`  
  • `target_id (FK → entities)`  
  • `rel_type` – one of 12 canonical verbs (`WORKS_AT`, `USES_TOOL`, …)  
  • `props` – JSONB (`role`, `since`, `confidence`, …).

- **conversations**  
  • `id (PK)`  
  • `user_id (FK)`  
  • `context_byte_id` – nullable FK when chat is attached to a doc.

- **messages**  
  • `id (PK)`  
  • `conversation_id (FK)`  
  • `role` – `'user' | 'assistant | tool'`  
  • `content` – JSON/raw  
  • `tool_name` – nullable.

- **subscriptions**  
  • `id (PK)`  
  • `user_id (FK)`  
  • Stripe price id, status, period_end.

---

## 2 JSON Schema Registry Pattern

> One file → `/schemas/byteSchemas.ts` keeps per‑item_type field specs.

```ts
export const BYTE_SCHEMAS = {
  recipe: {
    prep_min:  { type: 'int', min: 0, max: 300 },
    cook_min:  { type: 'int', min: 0, max: 300 },
    oven_temp_c: { type: 'int', min: 0, max: 400 },
    servings:  { type: 'int', min: 1, max: 20 },
  },
  paystub: {
    employer:  { type: 'string', maxLen: 120 },
    net_pay:   { type: 'float'  },
    currency:  { type: 'enum', values: ['USD','EUR','GBP'] },
    period_start: { type: 'date' },
    period_end:   { type: 'date' },
  },
};
```

*Validator rejects unknown keys → they fall into `properties.extra`.*

---

## 3 Core Tools (v0.1)

- **ByteCreate** – deterministic Python; arguments: `user_id`, `content_md`, `title?`, `item_type?`, `file_url?`, `hint?`.  
  • Writes `bytes` row  
  • Queues background jobs (EntitySuggest, ExtractProps, Embed)

- **EntitySuggest** – LLM NER → returns list of `{name,type}`.  
- **EntityCreate** – dedup + insert, returns `entity_id`.  
- **ExtractProperties** – uses BYTE_SCHEMAS to fill `bytes.properties`.  
- **ByteSearch** – vector + SQL filter.

---

## 4 Edge Vocabulary (keep ≤12)
`WORKS_AT, WORKS_ON, FOUNDED_BY, OWNED_BY,
 LOCATED_IN, PART_OF, EVENT_OF, ATTENDED,
 ABOUT, RELATED_TO, NEXT_STEP, USES_TOOL`

---

## 5 Index & Perf Notes

* pgvector index on `bytes.embedding` → `ivfflat lists=100`
* Composite index `(user_id, item_type)` on `bytes` for filters.
* RLS: every table checks `user_id = auth.uid()`; public rows use `user_id IS NULL`.

---

## 6 Background Workers (Celery / Bun queue)

1. **OCR + TextExtraction**  
2. **PropertyExtraction**  
3. **EntityPipeline**  
4. **EmbedChunker**  
5. **Nightly Dedupe & Edge‑merge**

---

> *Last updated 2025‑04‑28 by ChatGPT o3.*


# Grizz v0.1 — What "Done" Looks Like

> **Scope:** single‑user MVP (no teams), deployed to Vercel (frontend) + Fly.io (engine) + Supabase.  Everything here must work end‑to‑end before v0.1 tag.

---

## 0. TL;DR Checklist

- [ ] **Auth** – Supabase magic‑link, JWT sent to FastAPI.
- [ ] **Chat UI** – textarea + streamed responses.
- [ ] **Tools wired** – `ByteCreate`, `ByteSearch`, `QuestPlanner` (stub).  
      • ByteCreate does DB + background pipeline.
- [ ] **Bytes DB tables** – `bytes`, `byte_entity_links`, `entities` (+ pgvector columns).
- [ ] **Background workers** – OCR → ExtractProperties → Entity pipeline.
- [ ] **Embed summaries** – `text-embedding-3-small` on each Byte.
- [ ] **Realtime** – front‑end auto‑picks up new Bytes via Supabase channel.
- [ ] **Deployment scripts** – one‑click to prod.

Hit every checkbox and v0.1 is shippable.

---

## 1. Core User Stories & How They Flow

### 1.1  "Save this pay‑slip PDF"
1. **User** drags PDF + types: *"Save this payslip."*
2. **Chat agent** (system prompt + recent 10 turns) → calls **ByteCreate**.
3. **ByteCreate tool**
   - inserts into `bytes` (`item_type:"document"`, `file_url`, etc.)
   - queues **OCR job**
4. **Assistant** replies: *"Saved! Byte #123."*
5. Background jobs
   - OCR text → ExtractProperties → `net_pay`, `currency` …
   - spaCy → GPT normaliser → new entities (Amazon, Jane Doe) → links
   - summarise → embeddings
6. Side‑panel pops a *Payslip Nov 2025* card.

### 1.2  "That insight was 🔥 – save it"
1. Chat continues; assistant sends a long answer.
2. **User**: *"🔥 Save that as a byte."*
3. Same chat call → model copies last assistant message → `ByteCreate` (`item_type:"note"`).
4. Reply *"Done!"* – no OCR needed.

### 1.3  Quick Retrieval
*User:* "Search my bytes for 'net pay August'."
1. Agent calls **ByteSearch**:
   - vector embed query → pgvector similarity on `bytes.embedding`
2. Assistant streams titles + links.

### 1.4  Quest MVP (stub)
*User:* "Plan 2‑day Berlin coffee tour."
1. Chat agent invokes **QuestPlanner** tool (just echoes "Feature coming v0.2" for now).

---

## 2. Background Pipeline (after ByteCreate)

```mermaid
graph TD
  ByteCreate -->|task| OCR
  OCR --> ExtractProps
  ExtractProps --> EntitySuggest
  EntitySuggest -->|0..n| EntityCreate
  EntityCreate --> Embedding
  ExtractProps --> Embedding
```
*Workers live in one `worker.py`, run via Fly.io cron‑like process.*

---

## 3. Minimal Edge & Prop Rules (reminder)

- Create entities only for **proper nouns** likely reused.
- Use 12 edge verbs; anything else → `RELATED_TO`.
- Scalar facts (money, time, colour) → `bytes.properties`.

---

## 4. Non‑Goals for v0.1

- Teams / shared workspaces.
- Vector‑chunk table (`byte_chunks`).
- Full Quest orchestration.
- Graph‑RAG traversal past 1 hop.

Keep v0.1 thin; everything above must function with <500 ms chat latency & <$0.01 cost per interaction.

---

*End of spec — update responsibly*



# Grizz v0.1 — Operational Addenda

> Complements the "Data & Tools" + "What Done Looks Like" docs.  Copy env keys, RLS snippets, observability URLs straight from here when wiring infra / CI.

---

## 1  Env‑var Manifest (`.env.example`)

```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://your.supabase.co
SUPABASE_SERVICE_KEY=...
FLY_API_TOKEN=...
REDIS_URL=redis://default:pass@fly-redis.internal:6379
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
```

---

## 2  Row‑Level Security Cheat‑Sheet

```sql
-- bytes table
CREATE POLICY "bytes_owner_rls" ON bytes
  FOR ALL USING (user_id = auth.uid());

-- entities table (same pattern)
CREATE POLICY "entities_owner_rls" ON entities
  FOR ALL USING (user_id = auth.uid());
```
*Apply identical policy to `byte_links`, `byte_entity_links`, ...*

---

## 3  Background Worker Stack

| Component | Choice | Note |
|-----------|--------|------|
| Queue     | **Redis** (Fly Managed) | free, 256 MB plan|
| Worker    | **RQ** | `rq worker grizz` launches with image |
| Tasks     | OCR, ExtractProps, EntityPipeline, EmbedChunker |

### Trigger rules
- `EmbedChunker` only if `content_tokens > 3000` or `file_size_mb > 1`.
- OCR runs when `mime` starts with `image/` or `application/pdf`.

---

## 4  Observability

| Metric | Tool |
|--------|------|
| API & worker logs | Fly → **Grafana Loki** (autoconfig URL in dashboard) |
| DB slow queries   | `pg_stat_statements` extension + Supabase chart |
| Queue depth       | RQ Dashboard `/admin/rq` protected by JWT |

---

## 5  Smoke‑Tests (CI)

1. **Chat latency** – `curl /chat` must return ≤ 800 ms for "Ping".
2. **ByteCreate** – hitting `/chat` with "Save this" inserts exactly 1 row in `bytes`.
3. **RLS** – `select * from bytes` with another user's JWT returns 0 rows.
4. **Worker ping** – enqueue `echo` job; expect result in ≤ 10 s.

---

*Last updated 2025‑04‑28.*


# Grizz Monorepo Folder Structure (v0.1)

> **Goal:** enough specificity that Cursor/AI tools can generate files in the right place without second‑guessing.  Keep this hierarchy synced with `next.config.js`, Fly.io `Dockerfile`s, and RQ process names.

```
grizz/
├─ README.md
├─ .env.example
├─ package.json            # root scripts (lint, type‑check, dev:all)
├─ turbo.json              # ℹ️ optional Turbo repo config
├─ fly.toml                # Fly.io app‑wide settings
├─ supabase/               # migrations & SQL seeds
│  ├─ migrations/
│  │   └─ 20250428T1210_init.sql
│  └─ types.ts             # auto‑gen DB types (supabase gen)
│
├─ src/                    # application code
│  ├─ app/                 # \_app router (Next 14)
│  │   ├─ layout.tsx       # global providers (Theme, AuthCtx)
│  │   ├─ (marketing)/     # public landing pages
│  │   ├─ (dashboard)/
│  │   │   ├─ layout.tsx   # dashboard shell (sidebar)
│  │   │   ├─ page.tsx     # redirects → /bytes
│  │   │   ├─ bytes/       # Knowledge base grid
│  │   │   │   └─ page.tsx
│  │   │   ├─ document/[id]/page.tsx   # Editor w/ chat panel
│  │   │   ├─ chat/page.tsx            # Full‑screen chat
│  │   │   └─ settings/page.tsx        # profile, billing
│  │   └─ api/              # Edge Route Handlers (Server Actions)
│  │       ├─ chat/route.ts # `POST /api/chat`
│  │       ├─ bytes/route.ts# `POST /api/bytes`
│  │       └─ webhooks/stripe.ts
│  │
│  ├─ core/                # highly‑coupled UX building blocks
│  │   ├─ editor/          # TipTap setup, nodes, slash‑cmds
│  │   ├─ bytes/           # ByteCard, ByteGrid, filters
│  │   ├─ chat/            # ChatHistory, Composer, streaming hook
│  │   └─ layout/          # Resizable panels, topbar, etc.
│  │
│  ├─ features/            # plug‑and‑play vertical slices
│  │   ├─ auth/            # Supabase magic link flow
│  │   ├─ subscription/    # Stripe billing views
│  │   └─ sharing/         # public byte share page
│  │
│  ├─ components/
│  │   └─ ui/              # Button, Card, Modal (shadcn/ui)
│  │
│  ├─ hooks/               # useDebounce, useInfiniteScroll …
│  ├─ stores/              # Zustand stores (chat, bytes)
│  ├─ lib/
│  │   ├─ supabase.ts      # single Supabase createClient()
│  │   ├─ ai/              # wrapper that hits Agents SDK service
│  │   ├─ validators/      # JSON‑schema runtime checks
│  │   └─ utils/
│  └─ types/               # global TS types (DB, tools)
│
├─ workers/                # long‑running background processes
│  ├─ rq_worker.py         # entrypoint: OCR → ExtractProps → EntityPipeline
│  ├─ embedding_worker.py  # consumes `embed` queue, writes pgvector
│  └─ cron/cleanup.py      # nightly dedupe & edge merge
│
├─ packages/               # independent libs (optional publish)
│  └─ ai-sdk-wrapper/
│     ├─ index.ts          # thin OpenAI / Anthropic switcher
│     └─ tools/            # Tool spec builders (ByteCreateSpec …)
│
└─ scripts/
   ├─ dev:all.sh           # runs Next, RQ, webhook tunnel
   └─ migrate.sh           # Supabase migration shortcut
```

## Notable Conventions

- **Edge handlers only for latency‑critical routes** (`/api/chat`, `/api/bytes`). Heavy lifting shoveled to workers via Redis queue.
- **`core/` vs `features/`** – anything that can ship as a standalone npm feature goes in `features/`; things tightly bound to Grizz UX sit in `core/`.
- **`packages/ai-sdk-wrapper`** is framework‑agnostic → unit‑testable, publishable later.
- **Workers** run as separate Fly.io "process groups" (`fly scale count ocr=1`).

> *Last updated 2025‑04‑28 by ChatGPT o3*


# Jaw-Dropping Demo Flows (v0.2)

> These represent the ideal showcase demos that highlight the power of Grizz's knowledge graph and Quest agent capabilities. They will require browser tool integration and are targeted for post-MVP development.

## 1. Steve Jobs Learning Ladder (Research → Tweets → Video → Thumbnails)

**Flow Demonstration:**
1. **Request:** "I'm really interested about technology and how Apple develops all its computers. Can you create a quest for me? From the first Apple computer one, all the way to iPhone, with the timeline, all the things that happened... like a nice, maybe 15 minutes read."
2. **Output 1:** Knowledge Byte with comprehensive Apple history, timeline, and images
3. **Follow-up:** "Perfect. Now, can you turn this into a tweet thread for me?"
4. **Processing:** Agent analyzes user's previous successful tweets to match style/voice
5. **Output 2:** Tweet thread byte with optimized formatting and engagement hooks
6. **Follow-up:** "That was successful! I want to turn this into a YouTube video. Can you develop the script for me based on that?"
7. **Output 3:** Complete video script with B-roll suggestions, timing cues, etc.
8. **Follow-up:** "Can you create six different thumbnails for me?"
9. **Output 4:** Thumbnail design suggestions optimized for YouTube performance

**Key Technical Points:**
- All outputs are separate but connected bytes (via entity links)
- Each transformation leverages the knowledge graph
- Style adaptation based on user's existing content
- Progressive enhancement of the same core content

## 2. Market-Scout (Starter Story Founder Analysis)

**Flow Demonstration:**
1. **Request:** "Ingest the whole Starter Story channel and list every founder making >$1M ARR with links, revenue stats, and photos."
2. **Processing:**
   - Bulk ingestion of video transcripts
   - Entity extraction identifying founders, companies, and revenue figures
   - Enrichment with headshots and additional context
3. **Output:** Comprehensive, sortable founder dossier byte with:
   - Founder names and companies
   - Revenue figures with sources (video timestamps)
   - Business models and niches
   - Profile images
   - Ready for outreach, competitive analysis, or market research

**Key Technical Points:**
- Demonstrates automated content ingestion at scale
- Shows sophisticated entity extraction
- Creates structured data from unstructured content
- Provides actionable business intelligence

## 3. Traveler's Assistant (Smart Trip Planning)

**Flow Demonstration:**
1. **Request:** "Here's my ticket for my conference next week in Milan. Can you create a new byte for me with my tickets? I need to find a hotel ideally near the place of the event, check the weather, find some nice coffees I should go to, and any other fun activities."
2. **Processing:**
   - Extracts event location and dates from ticket
   - Researches hotels near venue
   - Checks weather forecast
   - Identifies high-rated cafés and activities
3. **Output:** Comprehensive travel byte containing:
   - Flight/ticket information
   - Weather forecast and packing suggestions
   - Hotel recommendations with booking links
   - Map with coffee shops and activities
   - Complete itinerary options

**Key Technical Points:**
- Transforms a single input (ticket) into comprehensive planning
- Demonstrates multi-source research (weather, maps, reviews)
- Creates immediately actionable recommendations
- Solves a universal pain point (travel planning complexity)

> These demos demonstrate Grizz's unique value proposition: transforming knowledge into connected, actionable outputs through the power of its entity-linked knowledge graph and intelligent Quest agent.


# Additional Demo Ideas

## CV-to-Job Matcher (Startup Outreach)

**Flow Demonstration:**
1. **Request:** "This is my CV. Find 10 small, scrappy startups where I'd be a good fit and could reach out directly to the founder."
2. **Processing:**
   - Analyzes CV for skills, experience, education, and industry focus
   - Researches startups matching the profile
   - Finds companies at appropriate stage/size
   - Identifies founder information
   - Creates personalized outreach messages
3. **Output:** Comprehensive job match byte containing:
   - 10 startups with company descriptions
   - Founder names, roles, and contact information 
   - Compatibility score with reasoning for each match
   - Personalized outreach message for each founder
   - Links to company websites/social profiles

**Key Technical Points:**
- Personally valuable with immediate actionable output
- Combines document analysis with targeted web research
- Demonstrates tailored content generation
- Universally relatable use case (job hunting)
- High viral potential ("This AI found me my dream job")

## Virtual Closet & Outfit Generator

**Flow Demonstration:**
1. **Request:** "I've uploaded photos of all my clothes. Help me create outfits for a 3-day business trip to New York next week."
2. **Processing:**
   - Organizes clothing items by category (tops, bottoms, shoes, accessories)
   - Checks New York weather forecast for next week
   - Applies style principles and event-appropriate combinations
   - Generates visual outfit compositions using user's actual clothes
3. **Output:** Fashion byte containing:
   - Daily outfit recommendations with weather considerations
   - Visual compositions showing how items work together
   - Mix-and-match alternatives for versatility
   - Packing checklist with everything needed

**Key Technical Points:**
- Highly visual, immediately shareable results
- Combines personal data with contextual intelligence (weather, events)
- Extreme viral potential ("This AI dressed me better than I dress myself")
- Universal appeal across demographics
- Drives daily engagement with each new outfit need


