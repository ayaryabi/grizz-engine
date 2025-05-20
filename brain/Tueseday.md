# Tuesday Plan – Async & Redis Migration Roadmap

_Reference: See @pt-arc.md for current architecture overview._

## Goal
Migrate from thread-pooled sync DB and in-process LLM calls to a scalable, async, Redis-queued architecture. This will allow us to handle thousands of users, decouple slow jobs, and scale horizontally on Fly.io.

---

## Step 1: Prep & Dependencies
- [ ] Provision a managed Redis instance (Upstash, Fly.io Redis, or Redis Cloud)
- [ ] Add `redis` and `asyncpg` to `requirements.txt`
- [ ] Review and update `.env` for Redis connection URL

---

## Step 2: Refactor Database Layer to Async
- [ ] Replace sync SQLAlchemy/psycopg2 with async SQLAlchemy/asyncpg in `app/db/database.py`
- [ ] Update all DB session usage to use `AsyncSession` and `await`
- [ ] Update all DB calls in services, agents, and API to use async/await
- [ ] Test: Write a simple async DB endpoint and verify it works

---

## Step 3: Integrate Redis Queue
- [ ] Add Redis connection code (using `redis-py`) to the project
- [ ] In WebSocket/HTTP handlers, push jobs (user message, metadata) to a Redis queue instead of processing immediately
- [ ] Define a clear job format (JSON: user_id, conversation_id, message, etc.)
- [ ] Test: Push and pull a test job from Redis in a script

---

## Step 4: Build Worker Process
- [ ] Create a new `worker.py` script
- [ ] Worker pulls jobs from Redis queue, processes them:
    - [ ] Calls OpenAI (async)
    - [ ] Saves result to DB (async)
    - [ ] Publishes result to Redis pub/sub (for streaming)
- [ ] Add error handling and logging
- [ ] Test: Run worker locally, verify it processes jobs and saves results

---

## Step 5: Real-Time Result Streaming
- [ ] In FastAPI, subscribe to Redis pub/sub for result updates
- [ ] Stream results back to the user via WebSocket as soon as they are available
- [ ] (Alternative: Implement polling if pub/sub is too complex for now)
- [ ] Test: End-to-end chat flow with streaming

---

## Step 6: Clean Up & Optimize
- [ ] Remove thread pool and sync DB code
- [ ] Update Dockerfile and Fly.io config if needed (e.g., to run multiple workers)
- [ ] Add health checks for Redis and async DB
- [ ] Update documentation (README, pt-arc.md)

---

## Step 7: Scale & Monitor
- [ ] Deploy to Fly.io with multiple workers
- [ ] Monitor Redis and DB performance
- [ ] Test with high concurrency (simulate 100s/1000s of users)
- [ ] Set up alerts for queue length, errors, and health checks

---

## Notes
- Tackle one step at a time; test after each major change.
- Use feature branches for each step if possible.
- Keep @pt-arc.md updated as the architecture evolves.

---

**This plan is your working checklist. Check off each item as you go!**
