# Workflow

Requirement Submission → Requirement Analysis → Audience/Competitor Research → Strategy → Content Generation → Compliance Review → Human Approval → Calendar/Content Package → Analytics → Report.

The six-agent execution is asynchronous in the web UI so users can observe `running`, `awaiting_human_approval`, `stopped` and `failed` states. Stop requests are honored between agent stages; a currently executing external/API call may finish before the workflow transitions to `stopped`.

Approval is a hard gate: `/api/content/{id}/publish` returns HTTP 409 until `approval_status=approved` and automated review has passed.

## Campaign control states

The UI separates internal database IDs from user-facing campaign numbers. Campaigns are displayed in creation order as Campaign #1, Campaign #2, etc., while API requests continue to use the internal numeric ID.

A campaign is initially `draft` / `not_started`. Clicking Run agents marks it `active` / `running`. When the six-agent workflow finishes it becomes `active` / `awaiting_human_approval`. The Stop action can be used for both a running workflow and an unused campaign; it changes the campaign to `stopped` so it no longer counts as active. The Dashboard polls campaign state automatically and the manual Refresh button provides an on-demand reload.
