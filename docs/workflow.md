# Workflow

Requirement Submission → Requirement Analysis → Audience/Competitor Research → Strategy → Content Generation → Compliance Review → Human Approval → Calendar/Content Package → Analytics → Report.

The six-agent execution is asynchronous in the web UI so users can observe `running`, `awaiting_human_approval`, `stopped` and `failed` states. Stop requests are honored between agent stages; a currently executing external/API call may finish before the workflow transitions to `stopped`.

Approval is a hard gate: `/api/content/{id}/publish` returns HTTP 409 until `approval_status=approved` and automated review has passed.
