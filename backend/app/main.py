from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.models import Campaign, ContentItem, ApprovalStep, AgentRun
from app.schemas.campaign import CampaignCreate, CampaignOut
from app.schemas.content import ContentUpdate, ApprovalRequest
from app.workflows.orchestrator import CampaignOrchestrator
from app.agents.analytics_agent import CampaignAnalyticsAgent
from app.agents.content_generation_agent import ContentGenerationAgent
from app.services.export_service import csv_bytes, pdf_bytes

import csv
import io
import json


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.1.0"
)


cors_origins = [
    x.strip()
    for x in settings.cors_origins.split(",")
    if x.strip()
]

production_origin = "https://agentic-ai-marketing-campaign-syste.vercel.app"

if production_origin not in cors_origins:
    cors_origins.append(production_origin)


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


orch = CampaignOrchestrator()


AGENT_NAMES = [
    "Marketing Requirement Analysis Agent",
    "Audience & Competitor Research Agent",
    "Campaign Strategy Agent",
    "Content Generation Agent",
    "Content Review & Brand Compliance Agent",
    "Campaign Analytics Agent"
]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode
    }


@app.get("/api/agents")
def agents():
    return {
        "agents": AGENT_NAMES
    }


@app.post("/api/campaigns", response_model=CampaignOut)
def create_campaign(
    data: CampaignCreate,
    db: Session = Depends(get_db)
):
    c = Campaign(
        **data.model_dump(exclude={"platforms"}),
        platforms=",".join(data.platforms)
    )

    db.add(c)
    db.commit()
    db.refresh(c)

    return c


@app.get("/api/campaigns", response_model=list[CampaignOut])
def list_campaigns(
    db: Session = Depends(get_db)
):
    return (
        db.query(Campaign)
        .order_by(Campaign.id.desc())
        .all()
    )


@app.get("/api/campaigns/{cid}", response_model=CampaignOut)
def get_campaign(
    cid: int,
    db: Session = Depends(get_db)
):
    c = db.get(Campaign, cid)

    if not c:
        raise HTTPException(404, "Campaign not found")

    return c


def brief(c):
    return {
        "product_name": c.product_name,
        "description": c.description,
        "target_audience": c.target_audience,
        "objective": c.objective,
        "budget": c.budget,
        "duration_days": c.duration_days,
        "platforms": [
            x for x in c.platforms.split(",") if x
        ],
        "brand_tone": c.brand_tone,
        "brand_guidelines": c.brand_guidelines
    }


def serialize_content(x):
    return {
        "id": x.id,
        "campaign_id": x.campaign_id,
        "platform": x.platform,
        "content_type": x.content_type,
        "topic": x.topic,
        "body": x.body,
        "approval_status": x.approval_status,
        "publishing_status": x.publishing_status,
        "review_status": x.review_status,
        "review_notes": x.review_notes,
        "scheduled_date": x.scheduled_date
    }


@app.post("/api/campaigns/{cid}/run")
def run_campaign(
    cid: int,
    db: Session = Depends(get_db)
):
    c = db.get(Campaign, cid)

    if not c:
        raise HTTPException(404, "Campaign not found")

    old_content_ids = [
        x.id
        for x in db.query(ContentItem.id)
        .filter(ContentItem.campaign_id == cid)
        .all()
    ]

    if old_content_ids:
        db.query(ApprovalStep).filter(
            ApprovalStep.content_id.in_(old_content_ids)
        ).delete(
            synchronize_session=False
        )

        db.query(ContentItem).filter(
            ContentItem.id.in_(old_content_ids)
        ).delete(
            synchronize_session=False
        )

    db.query(AgentRun).filter(
        AgentRun.campaign_id == cid
    ).delete(
        synchronize_session=False
    )

    result = orch.run_campaign(brief(c))

    c.workflow_status = "awaiting_human_approval"
    c.status = "active"
    c.projected_analytics = json.dumps(
        result.get("analytics", {})
    )

    outputs = {
        "Marketing Requirement Analysis Agent":
            result.get("campaign_brief"),

        "Audience & Competitor Research Agent":
            result.get("research"),

        "Campaign Strategy Agent":
            result.get("strategy"),

        "Content Generation Agent":
            result.get("content"),

        "Content Review & Brand Compliance Agent":
            result.get("reviewed_content"),

        "Campaign Analytics Agent":
            result.get("analytics")
    }

    for name in AGENT_NAMES:
        db.add(
            AgentRun(
                campaign_id=cid,
                agent_name=name,
                status="completed",
                output=json.dumps(
                    outputs.get(name, ""),
                    default=str
                )
            )
        )

    for item in result["reviewed_content"]:
        ci = ContentItem(
            campaign_id=cid,
            platform=item["platform"],
            content_type=item["content_type"],
            topic=item["topic"],
            body=item["body"],
            review_status=item["review_status"],
            review_notes=item["review_notes"],
            scheduled_date=item["scheduled_date"]
        )

        db.add(ci)
        db.flush()

        db.add(
            ApprovalStep(
                content_id=ci.id,
                status="pending"
            )
        )

    db.commit()

    return {
        "campaign_id": cid,
        "workflow_status": c.workflow_status,
        "agents": AGENT_NAMES,
        "strategy": result["strategy"],
        "research": result["research"],
        "analytics": result["analytics"],
        "content_count": len(result["reviewed_content"])
    }


@app.get("/api/campaigns/{cid}/research")
def research(
    cid: int,
    db: Session = Depends(get_db)
):
    c = db.get(Campaign, cid)

    if not c:
        raise HTTPException(404, "Campaign not found")

    result = orch.research.run(brief(c))

    return {
        "sources": result["research"],
        "personas": result["personas"]
    }


@app.get("/api/campaigns/{cid}/strategy")
def strategy(
    cid: int,
    db: Session = Depends(get_db)
):
    c = db.get(Campaign, cid)

    if not c:
        raise HTTPException(404, "Campaign not found")

    return orch.strategy.run(
        {"brief": brief(c)}
    )["strategy"]


@app.get("/api/campaigns/{cid}/content")
def content(
    cid: int,
    db: Session = Depends(get_db)
):
    return [
        serialize_content(x)
        for x in db.query(ContentItem)
        .filter(ContentItem.campaign_id == cid)
        .all()
    ]


@app.get("/api/campaigns/{cid}/calendar")
def calendar(
    cid: int,
    db: Session = Depends(get_db)
):
    return [
        serialize_content(x)
        for x in db.query(ContentItem)
        .filter(ContentItem.campaign_id == cid)
        .order_by(ContentItem.scheduled_date)
        .all()
    ]


@app.put("/api/content/{content_id}")
def edit_content(
    content_id: int,
    data: ContentUpdate,
    db: Session = Depends(get_db)
):
    x = db.get(ContentItem, content_id)

    if not x:
        raise HTTPException(404, "Content not found")

    x.body = data.body
    x.approval_status = "pending"
    x.publishing_status = "not_published"

    from app.agents.content_review_agent import (
        ContentReviewBrandComplianceAgent
    )

    campaign = db.get(Campaign, x.campaign_id)

    result = ContentReviewBrandComplianceAgent().run(
        {
            "brief": brief(campaign),
            "content": [
                {
                    "platform": x.platform,
                    "content_type": x.content_type,
                    "topic": x.topic,
                    "body": x.body,
                    "scheduled_date": x.scheduled_date
                }
            ]
        }
    )

    checked = result["reviewed_content"][0]

    x.review_status = checked["review_status"]
    x.review_notes = checked["review_notes"]

    db.commit()

    return {
        "status": "updated",
        "id": x.id,
        "review_status": x.review_status,
        "review_notes": x.review_notes
    }


@app.post("/api/content/{content_id}/approve")
def approve(
    content_id: int,
    data: ApprovalRequest,
    db: Session = Depends(get_db)
):
    x = db.get(ContentItem, content_id)

    if not x:
        raise HTTPException(404, "Content not found")

    if x.review_status not in (
        "approved_for_human_review",
        "passed",
        "approved"
    ):
        raise HTTPException(
            409,
            "Content must pass automated review before human approval."
        )

    x.approval_status = "approved"
    x.review_notes = data.comment or x.review_notes

    step = (
        db.query(ApprovalStep)
        .filter_by(content_id=content_id)
        .first()
    )

    if step:
        step.status = "approved"
        step.comment = data.comment

    campaign = db.get(Campaign, x.campaign_id)

    db.commit()

    if campaign:
        pending = (
            db.query(ContentItem)
            .filter(
                ContentItem.campaign_id == campaign.id,
                ContentItem.approval_status != "approved"
            )
            .count()
        )

        if pending == 0:
            campaign.workflow_status = "calendar_ready"
            db.commit()

    return {
        "status": "approved"
    }


@app.post("/api/content/{content_id}/reject")
def reject(
    content_id: int,
    data: ApprovalRequest,
    db: Session = Depends(get_db)
):
    x = db.get(ContentItem, content_id)

    if not x:
        raise HTTPException(404, "Content not found")

    x.approval_status = "rejected"
    x.review_notes = (
        data.comment or "Rejected for revision"
    )

    step = (
        db.query(ApprovalStep)
        .filter_by(content_id=content_id)
        .first()
    )

    if step:
        step.status = "rejected"
        step.comment = data.comment

    db.commit()

    return {
        "status": "rejected"
    }


@app.post("/api/content/{content_id}/regenerate")
def regenerate(
    content_id: int,
    db: Session = Depends(get_db)
):
    x = db.get(ContentItem, content_id)

    if not x:
        raise HTTPException(404, "Content not found")

    c = db.get(Campaign, x.campaign_id)

    if not c:
        raise HTTPException(404, "Campaign not found")

    b = brief(c)

    draft = ContentGenerationAgent()._generate(
        x.platform,
        b,
        x.topic,
        {}
    )

    x.body = draft
    x.approval_status = "pending"
    x.publishing_status = "not_published"

    from app.agents.content_review_agent import (
        ContentReviewBrandComplianceAgent
    )

    checked = ContentReviewBrandComplianceAgent().run(
        {
            "brief": b,
            "content": [
                {
                    "platform": x.platform,
                    "content_type": x.content_type,
                    "topic": x.topic,
                    "body": x.body,
                    "scheduled_date": x.scheduled_date
                }
            ]
        }
    )["reviewed_content"][0]

    x.review_status = checked["review_status"]
    x.review_notes = checked["review_notes"]

    db.commit()

    return {
        "status": "regenerated",
        "content": serialize_content(x)
    }


@app.post("/api/content/{content_id}/publish")
def publish(
    content_id: int,
    db: Session = Depends(get_db)
):
    x = db.get(ContentItem, content_id)

    if not x:
        raise HTTPException(404, "Content not found")

    if x.approval_status != "approved":
        raise HTTPException(
            409,
            "Publishing is blocked until human approval."
        )

    x.publishing_status = "published"

    db.commit()

    return {
        "status": "published"
    }


@app.post("/api/campaigns/{cid}/analytics")
def analytics(
    cid: int,
    data: dict,
    db: Session = Depends(get_db)
):
    c = db.get(Campaign, cid)

    if not c:
        raise HTTPException(404, "Campaign not found")

    result = CampaignAnalyticsAgent().run(data)

    if result.get("observed"):
        c.observed_analytics = json.dumps(result)
    else:
        c.projected_analytics = json.dumps(result)

    db.commit()

    return result


@app.post("/api/campaigns/{cid}/analytics/upload")
def analytics_upload(
    cid: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not db.get(Campaign, cid):
        raise HTTPException(
            404,
            "Campaign not found"
        )

    try:
        text = file.file.read().decode("utf-8-sig")
        rows = list(
            csv.DictReader(
                io.StringIO(text)
            )
        )
    except UnicodeDecodeError:
        raise HTTPException(
            400,
            "CSV must be UTF-8 encoded"
        )

    if not rows:
        raise HTTPException(
            400,
            "CSV contains no data rows"
        )

    keys = [
        "impressions",
        "engagements",
        "clicks",
        "conversions",
        "spending",
        "leads"
    ]

    missing = [
        k for k in keys
        if k not in (rows[0] or {})
    ]

    if missing:
        raise HTTPException(
            400,
            f"CSV is missing required columns: {', '.join(missing)}"
        )

    try:
        totals = {
            k: sum(
                float(r.get(k, 0) or 0)
                for r in rows
            )
            for k in keys
        }
    except (TypeError, ValueError):
        raise HTTPException(
            400,
            "CSV contains non-numeric KPI values"
        )

    if any(v < 0 for v in totals.values()):
        raise HTTPException(
            400,
            "CSV KPI values cannot be negative"
        )

    if (
        totals["engagements"] > totals["impressions"]
        or totals["clicks"] > totals["impressions"]
        or totals["conversions"] > totals["clicks"]
    ):
        raise HTTPException(
            400,
            "CSV KPI relationships are invalid: engagements/clicks cannot exceed impressions and conversions cannot exceed clicks"
        )

    totals["observed"] = True

    result = CampaignAnalyticsAgent().run(totals)

    c = db.get(Campaign, cid)
    c.observed_analytics = json.dumps(result)

    db.commit()

    return result


def report_data(
    cid,
    db
):
    c = db.get(Campaign, cid)

    if not c:
        raise HTTPException(
            404,
            "Campaign not found"
        )

    items = (
        db.query(ContentItem)
        .filter_by(campaign_id=cid)
        .all()
    )

    b = brief(c)

    runs = (
        db.query(AgentRun)
        .filter_by(campaign_id=cid)
        .all()
    )

    outputs = {
        r.agent_name: r.output
        for r in runs
    }

    try:
        strat = json.loads(
            outputs.get(
                "Campaign Strategy Agent",
                "{}"
            )
        )
    except Exception:
        strat = orch.strategy.run(
            {"brief": b}
        )["strategy"]

    try:
        research_data = json.loads(
            outputs.get(
                "Audience & Competitor Research Agent",
                "[]"
            )
        )
    except Exception:
        research_data = orch.research.run(
            b
        )["research"]

    analytics_data = (
        json.loads(
            c.observed_analytics or "{}"
        )
        or json.loads(
            c.projected_analytics or "{}"
        )
        or CampaignAnalyticsAgent().run(
            {
                "impressions": 10000,
                "engagements": 700,
                "clicks": 450,
                "conversions": 45,
                "spending": float(c.budget),
                "leads": 45,
                "observed": False
            }
        )
    )

    return (
        c,
        items,
        strat,
        research_data,
        analytics_data
    )


@app.get("/api/campaigns/{cid}/export/csv")
def export_csv(
    cid: int,
    db: Session = Depends(get_db)
):
    c, items, _, _, _ = report_data(
        cid,
        db
    )

    return Response(
        csv_bytes(items),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f"attachment; filename=campaign-{cid}.csv"
        }
    )


@app.get("/api/campaigns/{cid}/export/pdf")
def export_pdf(
    cid: int,
    db: Session = Depends(get_db)
):
    c, items, strat, research_data, analytics_data = report_data(
        cid,
        db
    )

    return Response(
        pdf_bytes(
            c,
            items,
            strat,
            research_data,
            analytics_data
        ),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f"attachment; filename=campaign-{cid}.pdf"
        }
    )


@app.get("/api/campaigns/{cid}/report")
def report(
    cid: int,
    db: Session = Depends(get_db)
):
    c, items, strat, research_data, analytics_data = report_data(
        cid,
        db
    )

    return {
        "campaign": brief(c),
        "strategy": strat,
        "research": research_data,
        "analytics": analytics_data,
        "content_calendar": [
            serialize_content(x)
            for x in items
        ],
        "approval": {
            "approved": sum(
                x.approval_status == "approved"
                for x in items
            ),
            "pending": sum(
                x.approval_status != "approved"
                for x in items
            )
        },
        "workflow_status": c.workflow_status
    }