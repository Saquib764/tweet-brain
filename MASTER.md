# Tweet Brain — Project Master

Internal source of truth for maintainers. Public overview lives in [README.md](README.md).

## Vision

Tweet Brain is a **personal, local-first** tool for growing your own X presence. It watches curated account groups, surfaces recent posts as news and inspiration, and runs configurable multi-step LLM workflows to produce tweet ideas and draft posts.

### Goals

- Track X accounts in named groups by category
- Fetch and cache recent posts locally (with date filtering)
- Run flexible, per-group LLM step pipelines (each step named and prompt-driven)
- Present everything in a dashboard with run history and markdown output
- Edit groups, members, and workflow steps from the UI (persisted to YAML)

### Non-goals (for now)

- Multi-user / hosted SaaS
- Posting tweets back to X
- Scheduled or background jobs
- Docker / cloud deployment

## Implementation status

| Area | Status |
|------|--------|
| YAML storage + atomic writes | Done |
| Default group seeding on first run | Done |
| X API fetch via xdk (user lookup + recent posts) | Done |
| Grok LLM via xAI OpenAI-compatible API | Done |
| Flexible N-step workflow pipeline | Done |
| Step-by-step and full-run execution | Done |
| Group CRUD (create, update, delete) | Done |
| Settings UI (X + xAI credentials) | Done |
| Dashboard: fetch, run, view output, run history | Done |
| Group editor: details, members, steps (drag-reorder) | Done |
| Backend tests (yaml_store) | Done |
| Scheduled fetch / automation | Not started |
| Post-to-X | Not started |

## Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Nuxt 4 (SPA), Nuxt UI 4, TypeScript, `marked` for markdown |
| Backend | FastAPI, Python 3.12+, uv |
| Storage | YAML files in `database/` |
| X API | [xdk](https://pypi.org/project/xdk/) Python SDK |
| LLM | Grok via [xAI API](https://docs.x.ai/) (OpenAI-compatible client) |

**Ports:** backend `8001`, frontend `80` (strict — fails if port unavailable).

## Architecture

```
┌─────────────┐     REST API      ┌──────────────┐
│ Nuxt UI     │ ◄──────────────► │ FastAPI       │
│ (SPA)       │                  │ Backend       │
└─────────────┘                   └──────┬───────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
              database/            X API (xdk)          api.x.ai (Grok)
              YAML files
```

**Typical flow:** Select group → Play → fetch posts (last N days) → start run → execute each step sequentially → view markdown output and run history.

## Repository layout

```
tweet-brain/
  backend/
    app/
      main.py              # FastAPI app, CORS, lifespan, health/version
      config.py            # Settings from env
      api/
        groups.py          # Group CRUD
        posts.py           # Fetch + cached posts
        workflows.py       # Runs, steps, history
        settings.py        # Credential management
      models/
        schemas.py         # Pydantic models + legacy migration
      services/
        yaml_store.py      # All YAML I/O
        pipeline.py        # Fetch + workflow orchestration
        twitter.py         # xdk wrapper
        llm.py             # xAI Grok client
        credentials.py     # Resolve + mask secrets
    default_groups.yaml    # Bundled seed (copied on first run)
  frontend/
    app/
      pages/
        index.vue          # Dashboard
        groups.vue         # Group editor
        settings.vue       # API credentials
      components/          # PostFeed, MarkdownContent, RunHistoryList, etc.
      composables/
        useTweetBrainApi.ts
      types/index.ts
    nuxt.config.ts
  database/                # Runtime data (gitignored except info.md)
    groups.yaml            # Created at runtime from default_groups.yaml
    settings.yaml          # API credentials (Settings UI)
    posts/{group_id}.yaml  # Cached fetches
    runs/{run_id}.yaml     # Workflow results
  README.md
  MASTER.md
```

- `database/*` is gitignored except `database/info.md`
- Seed data lives in `backend/default_groups.yaml`; copied to `database/groups.yaml` on startup when no groups exist
- Secrets in `database/settings.yaml` or `backend/.env` (never committed)

## Data model

### `database/groups.yaml`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | URL-safe slug, unique (auto-generated from name on create) |
| `name` | string | yes | Display name |
| `category` | string | yes | Dashboard grouping key |
| `description` | string | no | Short blurb |
| `members` | `{ account: string }[]` | yes | X usernames (no `@`) |
| `fetch.posts_per_user` | int | no | Default 10 |
| `steps.items` | `{ name, content }[]` | yes | Ordered workflow steps |

**Legacy migration:** `accounts` → `members`, `prompts` → `steps` (with `stem`/`combine`/`craft` synced to first three `items` entries) handled in `Group` and `GroupSteps` validators.

**Default seed group:** `researcher` — 6 AI researcher accounts, 2 steps (`Read` → `Story`).

### `database/settings.yaml`

| Field | Type | Description |
|-------|------|-------------|
| `x_api.bearer_token` | string | X API bearer token (xdk) |
| `xai.api_key` | string | xAI API key |
| `xai.model` | string | Grok model name (default `grok-4.3`) |

Gitignored at runtime. Configured via `/settings` UI. Stored values take precedence over `backend/.env` for the same field; env fills gaps. API GET responses mask secrets (last 4 chars visible).

### `database/posts/{group_id}.yaml`

| Field | Type | Description |
|-------|------|-------------|
| `group_id` | string | Matches group `id` |
| `fetched_at` | ISO datetime | Last fetch timestamp |
| `posts` | Post[] | Cached posts |

**Post object:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | X post ID |
| `author` | string | Username (no `@`) |
| `text` | string | Post text |
| `created_at` | string | ISO datetime from X |
| `url` | string | `https://x.com/{author}/status/{id}` (auto-filled if missing) |

### `database/runs/{run_id}.yaml`

Run ID format: `{YYYYMMDD-HHMMSS}-{group_id}`.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique run identifier |
| `group_id` | string | Source group |
| `started_at` | ISO datetime | Run start |
| `completed_at` | ISO datetime | Run end (null while running) |
| `status` | string | `running` \| `completed` \| `failed` |
| `stages.steps` | StepResult[] | `{ name, index, output }` per completed step |
| `stages.stem` | object[] | Legacy — `{ post_id, author, analysis }` |
| `stages.combine` | object | Legacy — `{ ideas: string[] }` |
| `stages.craft` | object | Legacy — `{ tweet: string }` |
| `error` | string | Present if `status=failed` |

Current pipeline writes only `stages.steps`. Legacy fields remain in schema for old run files.

## Workflow pipeline

### 1. Fetch

- **Input:** group `members`, `fetch.posts_per_user`, optional `days` query param (default 3)
- **Action:** xdk user lookup + `get_posts` per member; excludes retweets and replies; stops paging when posts older than cutoff
- **Output:** `database/posts/{group_id}.yaml`
- **Errors:** 503 if X credentials missing; 502 on X API failure; 404 if user not found

### 2. Run (N named steps)

Each group defines an ordered list of steps in `steps.items`. Step behavior:

| Step index | LLM system prompt | LLM user message |
|------------|-------------------|------------------|
| 0 | `steps.items[0].content` | Formatted block of all cached posts (author, ID, URL, date, text) |
| N > 0 | `steps.items[N].content` | Prior step's `output` string |

- LLM: Grok via xAI, temperature 0.7, system + user messages
- Each step appends a `StepResult` to `stages.steps`
- Run marked `completed` after the last step; `failed` + `error` on exception
- Steps must run in order (cannot skip ahead)

**Execution modes:**

- **Full run:** `POST /groups/{id}/run` — creates run, executes all steps sequentially
- **Step-by-step:** `POST /groups/{id}/runs` then `POST .../runs/{run_id}/steps/{index}` per step (used by dashboard Play button)

The bundled `researcher` group uses a 2-step pipeline: `Read` (themes + tweet ideas in markdown) → `Story` (narrative reply drafts per idea).

## API surface

Base prefix: `/api/v1` (configurable via `API_V1_PREFIX`).

### Health / meta

| Method | Path | Response |
|--------|------|----------|
| GET | `/health` | `{ status, service }` |
| GET | `/version` | `{ service, version, environment, uptime_seconds, x_api_configured, xai_configured }` |

### Groups

| Method | Path | Description |
|--------|------|-------------|
| GET | `/groups` | List groups with metadata (`last_fetched_at`, `post_count`, `last_run_at`, `last_run_status`) |
| POST | `/groups` | Create group (`name`, `category`, `description`); ID slugified from name |
| GET | `/groups/{id}` | Group with metadata |
| PUT | `/groups/{id}` | Full update (members, fetch, steps, etc.) |
| DELETE | `/groups/{id}` | Delete group (204) |

### Posts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/groups/{id}/posts` | Cached posts (404 if never fetched) |
| POST | `/groups/{id}/fetch?days=3` | Fetch live from X, save YAML, return cache |

### Workflows

| Method | Path | Description |
|--------|------|-------------|
| POST | `/groups/{id}/run` | Full workflow (all steps) |
| POST | `/groups/{id}/runs` | Start empty run (`status: running`) |
| POST | `/groups/{id}/runs/{run_id}/steps/{step_index}` | Execute one step |
| GET | `/runs?group_id=` | List run summaries (newest first) |
| GET | `/runs/{run_id}` | Full run detail |
| DELETE | `/runs/{run_id}` | Delete single run (204) |
| DELETE | `/groups/{id}/runs` | Delete all runs for group (204) |

### Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/settings` | `AppSettingsPublic` (masked secrets, configured flags) |
| PUT | `/settings` | Merge update into `database/settings.yaml` |

## Frontend UI

| Route | Page | Features |
|-------|------|----------|
| `/` | Dashboard | Group sidebar; Play (fetch + step-by-step run); step status indicators; output panel (posts feed or markdown per step); run history with load/delete |
| `/groups` | Group editor | Create/delete groups; sections: Details (name, category, description, posts per user), Members (add/remove X handles), Steps (add/remove/reorder via drag, edit prompts) |
| `/settings` | Settings | XDK bearer token; Grok API key + model; masked placeholders for existing secrets |

**Components:** `AppHeader` (nav), `PostFeed` (cached posts with @mention links), `MarkdownContent` (step output rendering), `RunHistoryList`, `GroupCard`, `WorkflowRunPanel`.

**API client:** `useTweetBrainApi()` composable; `NUXT_API_BASE` defaults to `http://localhost:8001`.

**Query params:** `?group=` on dashboard; `?id=&section=details|members|steps` on groups; `?section=xdk|grok` on settings.

## Backend services

| Service | Role |
|---------|------|
| `YamlStore` | Read/write groups, posts, runs, settings; atomic writes via temp file; `ensure_default_groups()` |
| `PipelineService` | `fetch_group_posts`, `start_run`, `execute_step`, `run_workflow` |
| `TwitterService` | xdk client; `get_user_recent_posts(username, limit, days)` |
| `LlmService` | xAI `chat.completions.create`; `complete(system, user)` |
| `credentials` | `resolve_credentials()` — settings.yaml then env fallback; `public_settings()` with masking |

## Configuration

### Environment variables (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `X_BEARER_TOKEN` | X API bearer token |
| `XAI_API_KEY` | xAI API key |
| `XAI_MODEL` | Grok model (default `grok-4.3`) |
| `DATABASE_ROOT` | Path to `database/` (default `../database`) |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `API_V1_PREFIX` | API prefix (default `/api/v1`) |
| `LOG_LEVEL` | Logging level (default `INFO`) |
| `ENVIRONMENT` | `development` enables LAN CORS regex for local network access |

### Frontend env

| Variable | Description |
|----------|-------------|
| `NUXT_API_BASE` | Backend URL (default `http://localhost:8001`) |

## Testing

```bash
cd backend && uv run pytest
```

Current coverage: `tests/test_yaml_store.py` — groups list/seed, posts/runs round-trip, run deletion.

## Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| **1 — Scaffold** | YAML store, API routes, dashboard shell, docs | Done |
| **2 — Live fetch** | xdk integration with date filtering | Done |
| **3 — Workflow UI** | Run pipeline from UI, markdown output, run history | Done |
| **4 — Group editing** | CRUD groups/members/steps in UI | Done |
| **5 — Automation** | Scheduled fetch, optional post-to-X | Planned |

## Open decisions

| Topic | Current default | Notes |
|-------|-----------------|-------|
| Posts per user | 10 | Configurable per group |
| Fetch window | 3 days | `days` query param on fetch endpoint |
| Rate limits | Fail with clear error | Retry/backoff TBD |
| Step count | Unbounded | UI and API support any number of steps; legacy 3-step stem/combine/craft still migrates |
| Default Grok model | `grok-4.3` | Override via settings or `XAI_MODEL` |
| Credential source | settings.yaml > .env | Env used when settings field empty |
