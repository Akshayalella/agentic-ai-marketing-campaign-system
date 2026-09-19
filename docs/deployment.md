# Deployment

## Render

Deploy `backend` as a Python web service and provide a managed PostgreSQL database.

Set:
`DATABASE_URL`, `DEMO_MODE`, `LLM_PROVIDER`, `OPENAI_API_KEY`, `RESEARCH_PROVIDER`, `CORS_ORIGINS`.

Start command:
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Vercel

Deploy the `frontend` directory.

Set:
`VITE_API_BASE_URL=https://YOUR-RENDER-BACKEND`

Then update backend `CORS_ORIGINS` to the Vercel origin.

## Docker

From repository root:
`docker compose -f docker/docker-compose.yml up --build`
