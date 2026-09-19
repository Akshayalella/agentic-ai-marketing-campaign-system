# API

Core endpoints:

- `GET /health`
- `GET /api/agents`
- `POST /api/campaigns`
- `GET /api/campaigns`
- `POST /api/campaigns/{id}/run`
- `GET /api/campaigns/{id}/research`
- `GET /api/campaigns/{id}/strategy`
- `GET /api/campaigns/{id}/content`
- `GET /api/campaigns/{id}/calendar`
- `PUT /api/content/{id}`
- `POST /api/content/{id}/approve`
- `POST /api/content/{id}/reject`
- `POST /api/content/{id}/regenerate`
- `POST /api/content/{id}/publish`
- `POST /api/campaigns/{id}/analytics`
- `POST /api/campaigns/{id}/analytics/upload`
- `GET /api/campaigns/{id}/report`
- `GET /api/campaigns/{id}/export/pdf`
- `GET /api/campaigns/{id}/export/csv`

Publishing returns HTTP 409 unless the content has been human-approved.
