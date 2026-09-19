# Agentic AI Marketing Campaign & Content Generation System

A full-stack six-agent marketing campaign system aligned to the supplied specification.

## Agent workflow

1. Marketing Requirement Analysis Agent
2. Audience & Competitor Research Agent
3. Campaign Strategy Agent
4. Content Generation Agent
5. Content Review & Brand Compliance Agent
6. Campaign Analytics Agent

Workflow:

`Requirements → Research → Strategy → Content → Compliance Review → Human Approval → Calendar → Analytics → Final Report`

The workflow uses shared state so each agent's output can be inspected. Publishing is blocked until explicit human approval.

## Improvements in this version

- Campaign pages now use the selected campaign instead of hard-coded campaign ID `1`.
- Re-running a campaign replaces its generated package instead of creating duplicate content.
- Strategy output includes objectives, audience segments, channel strategy, cadence, phased timeline, KPIs and budget allocation.
- Budget allocation is weighted by platform and corrected so totals equal the campaign budget.
- Content generation supports an OpenAI LLM provider with a deterministic demo fallback.
- Generated content is checked for unsupported absolute claims, unsourced percentage claims, missing content and supplied brand rules.
- Projected and observed analytics are persisted separately; observed CSV data is used in reports after upload.
- The human approval gate is tested through the actual API: publish fails before approval and succeeds after approval.
- Human edits and regenerated drafts are automatically re-reviewed before they can be approved.
- Campaign reruns remove dependent approval records before replacing generated content, preserving PostgreSQL foreign-key integrity.
- Analytics CSV uploads validate required columns, numeric values, non-negative KPIs and basic KPI relationships.
- Research uses the configured web provider by default and clearly labels demo fallback results.

## Features

- FastAPI + Pydantic backend
- React + TypeScript frontend
- SQLAlchemy persistence with PostgreSQL-compatible configuration and SQLite local default
- Six specialized AI agents
- Configurable OpenAI/Demo LLM provider
- Web research with source references and demo fallback
- LinkedIn, Email and Instagram content
- Multi-day content calendar
- Brand/claim review
- Human edit/approve/reject/regenerate workflow
- Hard publishing approval gate
- Projected vs observed KPI analytics
- CSV performance upload
- PDF/CSV export
- Docker Compose
- Five required scenario tests plus API approval-gate coverage
- Architecture SVG and documentation

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
# activate the environment
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run build
npm run dev
```

### Docker

```bash
docker compose up --build
```

## Environment

Copy `backend/.env.example` to `backend/.env` and configure:

- `DATABASE_URL`
- `DEMO_MODE`
- `LLM_PROVIDER`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `RESEARCH_PROVIDER`
- `CORS_ORIGINS`

The frontend uses `VITE_API_BASE_URL`.

## Research

`RESEARCH_PROVIDER=web` uses a keyless DuckDuckGo Instant Answer integration when network access is available. If it cannot retrieve results, the application returns clearly labelled demo sources rather than presenting them as verified research.

## Analytics

Projected analytics are generated for planning and explicitly labelled as projected. Upload a CSV with columns such as:

`impressions, engagements, clicks, conversions, spending, leads`

The resulting observed KPIs are stored with the campaign and used in the campaign report/export.

## Testing

The backend test suite covers:

- TC-01 product launch campaign
- TC-02 LinkedIn-only campaign
- TC-03 limited-budget campaign
- TC-04 unsupported product claim
- TC-05 performance KPI calculations
- research source structure
- strategy output completeness
- real publish approval gate

In the local validation environment, the backend suite completed with **12 passing tests**. The frontend dependency installation/build could not be completed in the restricted environment because package downloads were unavailable; the project includes the required TypeScript React type dependencies for a normal `npm install && npm run build`.

## Documentation

- `docs/architecture.md`
- `docs/architecture.svg`
- `docs/agents.md`
- `docs/workflow.md`
- `docs/api.md`
- `docs/deployment.md`
