# Grizz Engine

An AI brain-service powering the Grizz writing companion. Turns chat messages into structured knowledge (Bytes), retrieves that knowledge on demand, and runs multi-step Quests to auto-generate new Bytes.

## Architecture

- **UI**: Next.js 14 (Chat pane, Bytes Hub, Quest launcher)
- **Backend**: FastAPI microservice (hosts the Manager agent, tools, and sub-agents)
- **Database**: Postgres + pgvector (Supabase)
- **Deployment**: Docker Compose (spins the trio `ui`, `engine`, `db` locally & in CI)

## Core Features

- ByteCreate: Save knowledge, extract entities, insert links
- ByteSearch: Vector + tag search for Bytes
- QuestGenerate: Multi-step content generation pipeline

## Development Roadmap

See [brain.md](brain.md) for the complete technical and product specification. 