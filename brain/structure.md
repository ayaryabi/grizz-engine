# Grizz Engine - Project Structure

## Folder Structure Overview

```
grizz-engine/
├── web/                       # Next.js web application
├── engine/                    # FastAPI AI brain service
├── shared-types/              # Shared type definitions
├── db/                        # Database migrations (Alembic/Supabase)
├── infra/                     # Infrastructure config
├── tests/                     # Test directories
├── docker-compose.yml         # At root for easy discovery
├── .env.example               # Document required env vars
└── .github/workflows/ci.yml   # CI pipeline
```

## Key Structure Decisions

| Component | Structure | Rationale |
|-----------|-----------|-----------|
| `web/` + `engine/` split | Two separate applications in one repo | Separates concerns while keeping codebase unified |
| Root `shared-types/` folder | Contains TypeScript enums, Pydantic models | Single source of truth prevents type drift |
| Root `docker-compose.yml` | Moved from `infra/docker/` | Developers expect it at the root; simplifies commands |
| `db/migrations/` | Using Alembic or Supabase SQL | Proper migration tooling instead of raw SQL files |
| `engine/app/agents/` | Contains `manager.py` & `subagents/` | Keeps Outliner/Drafter isolated for performance tuning |
| `engine/app/tools/` | Co-located JSON schemas and code | Pairs like `my_tool.py` + `my_tool.json` for easier maintenance |
| `web/lib/supabase/` | Renamed from `web/lib/db/` | Clearly indicates Supabase client, not direct Postgres |
| Root `.env.example` | Documents all required env vars | Streamlines onboarding with copy→paste→go |
| `tests/` folders | Separate test setup for each component | UI uses Playwright/vitest; engine uses pytest |
| `.github/workflows/ci.yml` | Single CI pipeline | Builds both Dockerfiles, runs all tests, atomic deployments |

## Benefits of This Structure

- **Developer Experience**: Intuitive organization, standard locations
- **Performance**: Logical separation enables isolated performance tuning
- **Maintenance**: Co-located related files, clear dependencies
- **CI/CD**: Single pipeline ensures full-stack health
- **Onboarding**: Clear documentation of environment setup
- **Type Safety**: Shared types prevent interface drift

This structure balances separation of concerns with the benefits of a monorepo approach. 