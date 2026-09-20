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

- Campaign pages use a persisted selected campaign instead of a hard-coded campaign ID.
- Campaign controls now support Select, Run agents, Stop and Delete with clear status/error feedback.
- Agent execution runs in the background for the web UI and can be stopped between workflow stages.
- Re-running a campaign replaces its generated package instead of creating duplicate content.
- Strategy output includes objectives, audience segments, channel strategy, cadence, phased timeline, KPIs and budget allocation.
- Budget allocation is weighted by platform and corrected so totals equal the campaign budget.
- Content generation supports an OpenAI LLM provider with a deterministic demo fallback.
- Generated content is checked for unsupported absolute claims, unsourced percentage claims, missing content and supplied brand rules.
- Projected and observed analytics are persisted separately; observed CSV data is used in reports after upload.
- Analytics now include a comparable 0–100 performance score plus target comparison; projected and observed datasets can produce different scores.
- The human approval gate is tested through the actual API: publish fails before approval and succeeds after approval.
- Human edits and regenerated drafts are automatically re-reviewed before they can be approved.
- Campaign reruns remove dependent approval records before replacing generated content, preserving PostgreSQL foreign-key integrity.
- Analytics CSV uploads validate required columns, numeric values, non-negative KPIs and basic KPI relationships, and preserve target comparisons supplied by the UI.
- Research uses the configured web provider by default and clearly labels demo fallback results.

## Brand consistency & reviewer mechanism

The Content Review & Brand Compliance Agent runs automatically after content generation and again after every human edit or regeneration. It produces a `review_status` and `review_notes` that are stored with each content item. Human approval is separate from automated review; content must pass automated review before it can be approved, and publishing is blocked until human approval is recorded.

The reviewer checks:

- missing/empty content;
- unsupported or absolute claims such as guarantees and ranking claims;
- percentage claims without visible source attribution;
- prohibited terms specified in brand guidelines using instructions such as `avoid`, `do not use`, or `prohibited`;
- required phrases specified with `must include`, `should include`, or `required phrase`;
- maximum character or word limits;
- explicit `no emojis` guidance;
- basic professional/formal/corporate tone conflicts such as common slang.

Example brand guidance:

```text
Professional tone. Avoid the word cheap. Must include Learn more.
Maximum 120 characters. No emojis.
```

A violation is returned as `rejected` with reviewer notes explaining the failed rule. A compliant draft receives `approved_for_human_review`, which still requires a human approval action before publishing.

This is a deterministic validation layer, not a claim that every possible semantic brand preference can be automatically understood. LLM-generated content is therefore always subject to the reviewer and human approval gate.

## Agent architecture and prompt responsibilities

The six specialized agents communicate through the orchestrator's shared campaign state. The main state fields are `campaign_brief`, `research`, `strategy`, `content`, `reviewed_content`, and `analytics`.

| Agent | Input | Main output |
|---|---|---|
| Requirement Analysis | User campaign form | Structured campaign brief |
| Audience & Competitor Research | Campaign brief | Personas, competitor/trend findings, source references |
| Campaign Strategy | Brief + research | Objectives, theme, channels, timeline, budget, KPIs |
| Content Generation | Brief + strategy | Platform-specific content |
| Content Review & Brand Compliance | Brief + generated content | Review status and compliance notes |
| Campaign Analytics | Performance data / planning inputs | Projected or observed KPIs |

Prompt responsibilities are documented in `docs/agents.md`. The content-generation instruction explicitly prohibits invented statistics, guarantees, rankings, customers, certifications and unsupported capabilities. The reviewer is intentionally deterministic so the approval gate does not depend only on an LLM opinion.

## Agent-to-agent communication and workflow state

The LangGraph orchestrator passes a shared state from one agent to the next:

```text
Campaign input
   -> Requirement Analysis
   -> Research
   -> Strategy
   -> Content Generation
   -> Compliance Review
   -> Human Approval
   -> Calendar / Publishing
   -> Analytics
   -> Report / Export
```

Projected analytics may be produced during planning. Observed analytics are written only after a validated performance dataset is uploaded. Human approval is enforced by the API before publishing.

## Database design

The application uses SQLAlchemy models with PostgreSQL-compatible configuration and SQLite as the local default. The core relational model is:

```text
Campaign
  | 1
  |----< ContentItem
  |          | 1
  |          `----< ApprovalStep
  |
  |----< AgentRun
  |
  |---- projected_analytics (JSON)
  `---- observed_analytics  (JSON)
```

### Main tables

- **Campaign** — product, description, audience, objective, budget, duration, platforms, brand tone/guidelines, workflow status and projected/observed analytics.
- **ContentItem** — platform, content type, topic, body, scheduled date, automated review status/notes, human approval status and publishing status.
- **ApprovalStep** — approval state and reviewer comment for each content item.
- **AgentRun** — campaign, agent name, execution status and serialized agent output for traceability.

Generated content and approval records are replaced safely when a campaign is rerun, including deletion of dependent approval rows before content replacement for PostgreSQL foreign-key integrity.

## Analytics calculations

For observed performance data, the analytics agent calculates:

- Engagement rate = `engagements / impressions × 100`
- Click-through rate = `clicks / impressions × 100`
- Conversion rate = `conversions / clicks × 100`
- Cost per lead = `spending / leads`
- Campaign spending = `spending`

Uploaded CSV data is validated for required columns, numeric values, non-negative metrics and basic relationships such as engagements/clicks not exceeding impressions and conversions not exceeding clicks.

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

In the local validation environment, the backend suite completed with **26 passing tests**, including campaign-control, approval-gate, brand-guideline and analytics-score coverage. The frontend build was previously validated with `npm run build`; in this restricted validation environment a fresh dependency download was unavailable, so the final frontend changes were also reviewed statically.

## Documentation

- `docs/architecture.md`
- `docs/architecture.svg`
- `docs/agents.md`
- `docs/workflow.md`
- `docs/api.md`
- `docs/deployment.md`

## Final submission checklist

Before submitting, verify the deployed application end-to-end rather than relying only on unit tests:

1. Create a product-launch campaign and run the six-agent workflow.
2. Confirm the Content Studio shows platform, content type, topic, generated content, automated reviewer status and reviewer notes.
3. Edit a content item and save it. Confirm it returns to `pending` approval and is re-reviewed.
4. Try to publish before approval. The API must return HTTP 409 and must not publish.
5. Approve a reviewed item, then publish it. Confirm publishing status changes to `published`.
6. Open Content Calendar and verify Date, Platform, Content type, Topic, Caption/Content, Approval status and Publishing status are all visible.
7. Upload `sample_data/performance.csv` and verify observed Engagement Rate, CTR, Conversion Rate, CPL and Spending.
8. Download both PDF and CSV reports and verify the exported content is present.
9. Run all five required scenarios and record the results in the submission evidence.
10. Verify the deployed Vercel frontend can reach the deployed FastAPI backend using `VITE_API_BASE_URL` and backend `CORS_ORIGINS`.
11. Record a 3–5 minute demonstration showing the complete workflow. If live research or OpenAI credentials are not configured, explicitly identify the labelled demo fallback instead of presenting it as live data.

### Required test evidence

| Test | Expected evidence | Status to record after deployed verification |
|---|---|---|
| TC-01 Product launch | Complete strategy with objectives, audience, channels, budget and KPIs | PASS / FAIL |
| TC-02 LinkedIn-only | LinkedIn-specific content only | PASS / FAIL |
| TC-03 Limited budget | Budget-aware allocation and total equal to supplied budget | PASS / FAIL |
| TC-04 Unsupported claim | Reviewer flags unsupported claim and blocks approval | PASS / FAIL |
| TC-05 Performance dataset | KPI values match uploaded sample data | PASS / FAIL |
| Approval gate | Publish returns 409 before approval and succeeds after approval | PASS / FAIL |
| Calendar fields | All seven required calendar fields are visible | PASS / FAIL |
| Export | PDF and CSV download successfully | PASS / FAIL |

Do not mark a deployment test as PASS until it has been executed against the deployed frontend/backend.


## Requirement coverage checklist

| Requirement | Implementation |
|---|---|
| Campaign creation | Product, audience, objective, budget, duration, platforms, tone and brand guidelines form |
| Automated research | Configurable web research provider with source URL, verification flag and clearly labelled demo fallback |
| Strategy | Objectives, audience segments, theme, channels, content strategy, timeline, budget allocation and KPIs |
| Multi-platform content | LinkedIn, Email and Instagram with platform-specific prompts/fallbacks |
| Content calendar | Date, platform, content type, topic, body, approval status and publishing status |
| Brand consistency | User-provided guidelines parsed for prohibited terms, required phrases, length, emoji and basic tone rules |
| Human approval | Review, edit, regenerate, reject and approve actions; publish API hard-blocks unapproved content |
| Analytics | CSV upload plus KPI calculation, optional target comparison, optional period trends and improvement suggestions |
| Reviewer | Missing content, unsupported/absolute claims, unsourced percentage claims and brand-rule violations |
| Export | PDF and CSV containing strategy, research, calendar, generated content and analytics |
| Required pages | Dashboard, Create Campaign, Audience Research, Campaign Strategy, Content Studio, Content Calendar, Approval Center, Analytics and Reports |

### Analytics formulas

- Engagement rate = engagements / impressions × 100
- Click-through rate = clicks / impressions × 100
- Conversion rate = conversions / clicks × 100
- Cost per lead = spending / leads
- Campaign spending = total spending

The analytics agent also supports optional numeric targets and previous-period values so it can report target status, trends and improvement suggestions. Projected metrics are kept separate from observed uploaded campaign data.

### Database design

The application persists campaigns and their generated package in PostgreSQL in deployment (SQLite is available as a local development fallback):

```text
Campaign
 ├── ContentItem
 │    └── ApprovalStep
 └── AgentRun
```

Campaign records store projected and observed analytics separately. Content records store platform, type, topic, body, scheduled date, automated review status/notes, human approval status and publishing status.

### Prompt and agent documentation

`docs/agents.md` describes each specialized agent's inputs, outputs and prompt responsibilities. The content-generation prompt prohibits invented statistics, guarantees, rankings, customers, certifications and unsupported capabilities. The reviewer is deterministic so the publishing gate is not dependent only on an LLM opinion.

### Campaign controls

The web UI supports selecting a campaign, starting the six-agent workflow asynchronously, stopping it between agent stages, and deleting a completed/stopped campaign. Re-running replaces the prior generated package to avoid duplicates.

### Analytics score

The 0–100 performance score is computed from engagement rate, CTR, conversion rate and CPL against fixed comparison benchmarks so projected and observed results remain comparable. User-entered targets are shown separately in target comparison and do not artificially force both scores to 100.

### Final verification

Before submission, run:

```text
cd backend
pytest -q

cd ../frontend
npm install
npm run build
```

Then test the five required scenarios and verify the deployed Vercel frontend can reach the deployed Render API. The demo video/live demonstration should show campaign creation, research, strategy, platform-specific content, reviewer findings, human approval/publish protection, analytics and exports.
