# Submission Verification Checklist

## A. Functional verification

- [ ] Create Campaign works in deployed frontend.
- [ ] Six-agent workflow completes.
- [ ] Campaign list supports Select, Run agents and Delete.
- [ ] Running campaigns show Stop and stop requests change the workflow to `stopped`.
- [ ] Research page displays sources/personas.
- [ ] Strategy page displays objectives, audience, channels, timeline, KPIs and budget.
- [ ] Content Studio generates LinkedIn, Email and Instagram content when those platforms are selected.
- [ ] Reviewer status and notes are visible for every content item.
- [ ] Human edit triggers automated re-review.
- [ ] Human approval is required before publishing.
- [ ] Publishing before approval is rejected by the backend with HTTP 409.
- [ ] Approved content can be published.
- [ ] Content Calendar shows Date, Platform, Content type, Topic, Caption/Content, Approval and Publishing status.
- [ ] Analytics CSV upload succeeds for the supplied sample data.
- [ ] Analytics displays Engagement Rate, CTR, Conversion Rate, CPL and Spending.
- [ ] Analytics displays a 0–100 performance score and projected/observed scores can differ.
- [ ] PDF export works.
- [ ] CSV export works.

## B. Required scenarios

- [ ] TC-01 Product launch campaign.
- [ ] TC-02 LinkedIn-only campaign.
- [ ] TC-03 Limited marketing budget.
- [ ] TC-04 Unsupported product claim.
- [ ] TC-05 Campaign performance dataset.

## C. Deployment

- [ ] Backend `/health` returns HTTP 200.
- [ ] Frontend `VITE_API_BASE_URL` points to the deployed backend.
- [ ] Backend `CORS_ORIGINS` contains the deployed Vercel origin.
- [ ] Database is persistent in the deployed environment.
- [ ] No production secrets are committed to GitHub.

## D. Submission evidence

- [ ] GitHub repository URL.
- [ ] Vercel frontend URL.
- [ ] Render/FastAPI backend URL.
- [ ] `docs/architecture.svg`.
- [ ] Sample campaign screenshots/data.
- [ ] Test results.
- [ ] 3–5 minute demonstration video or live demonstration.


## Final local verification
- Backend test suite: `pytest -q` (expected: all tests pass)
- Frontend production build: `npm install` then `npm run build`
- Confirm no local `marketing.db`, `__pycache__`, or `.pytest_cache` files are committed.
