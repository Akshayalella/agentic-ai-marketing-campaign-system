# Six-agent architecture

1. Marketing Requirement Analysis — converts campaign input into a structured brief.
2. Audience & Competitor Research — produces personas, competitor/trend research and source references; demo sources are explicitly marked unverified.
3. Campaign Strategy — defines theme, channels, timeline, budget allocation and KPIs.
4. Content Generation — creates platform-specific LinkedIn, Email and Instagram content.
5. Content Review & Brand Compliance — flags unsupported claims and tone/brand issues.
6. Campaign Analytics — calculates observed/projected engagement rate, CTR, conversion rate, CPL and spend.


## Prompt responsibilities

- **Requirement Analysis:** extract product, audience, objective, budget, duration, platforms and brand constraints into structured state.
- **Research:** search the configured provider and return source title, URL, summary, verification flag and source type; hypothetical personas remain marked unverified.
- **Strategy:** transform the structured brief and research into objectives, audience segments, channel strategy, cadence, phased timeline, budget allocation and KPIs.
- **Content:** create original platform-specific copy using the approved brief and strategy; do not invent statistics, guarantees, rankings, customers, certifications or unsupported capabilities.
- **Review:** check missing content, absolute/unsupported claims, unsourced percentage claims and supplied brand constraints before human approval.
- **Analytics:** calculate engagement rate, CTR, conversion rate, cost per lead and spending; optionally compare metrics with predefined targets and previous-period values; return trend changes and improvement suggestions; preserve projected and observed results separately.


## Reviewer rule examples

The reviewer accepts explicit brand instructions in natural-language guidelines and translates supported patterns into deterministic checks. Examples include:

- `Avoid the word cheap` -> flags `cheap` when present.
- `Must include Learn more` -> flags drafts missing `learn more`.
- `Maximum 120 characters` -> flags longer drafts.
- `Maximum 80 words` -> flags longer drafts.
- `No emojis` -> flags common Unicode emoji ranges.
- `Professional`, `formal`, or `corporate` tone -> flags a small configured set of common slang terms.

Unsupported or absolute claims and unsourced percentage claims are also checked independently of the supplied guidelines. Reviewer output is persisted as `review_status` and `review_notes`; automated pass does not equal human approval.
