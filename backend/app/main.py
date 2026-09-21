from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import Base, engine, get_db, SessionLocal
from app.models import Campaign, ContentItem, ApprovalStep, AgentRun
from app.schemas.campaign import CampaignCreate, CampaignOut
from app.schemas.content import ContentUpdate, ApprovalRequest
from app.workflows.orchestrator import CampaignOrchestrator, WorkflowStopped
from app.agents.analytics_agent import CampaignAnalyticsAgent
from app.agents.content_generation_agent import ContentGenerationAgent
from app.services.export_service import csv_bytes, pdf_bytes
import csv, io, json, threading
from concurrent.futures import ThreadPoolExecutor

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(',') if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
orch = CampaignOrchestrator()
executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="campaign-worker")
running_events: dict[int, threading.Event] = {}
running_lock = threading.Lock()

AGENT_NAMES = [
    "Marketing Requirement Analysis Agent", "Audience & Competitor Research Agent",
    "Campaign Strategy Agent", "Content Generation Agent",
    "Content Review & Brand Compliance Agent", "Campaign Analytics Agent"
]


def _error_message(exc):
    detail = getattr(getattr(exc, "response", None), "data", None)
    if isinstance(detail, dict) and detail.get("detail"):
        return str(detail["detail"])
    return "Request failed. Please try again."


def brief(c):
    return {
        "product_name": c.product_name,
        "description": c.description,
        "target_audience": c.target_audience,
        "objective": c.objective,
        "budget": c.budget,
        "duration_days": c.duration_days,
        "platforms": [x for x in c.platforms.split(",") if x],
        "brand_tone": c.brand_tone,
        "brand_guidelines": c.brand_guidelines,
    }


def serialize_content(x):
    return {
        "id": x.id, "campaign_id": x.campaign_id, "platform": x.platform,
        "content_type": x.content_type, "topic": x.topic, "body": x.body,
        "approval_status": x.approval_status, "publishing_status": x.publishing_status,
        "review_status": x.review_status, "review_notes": x.review_notes,
        "scheduled_date": x.scheduled_date,
    }


def _prepare_campaign(db, c):
    old_content_ids = [x.id for x in db.query(ContentItem.id).filter(ContentItem.campaign_id == c.id).all()]
    if old_content_ids:
        db.query(ApprovalStep).filter(ApprovalStep.content_id.in_(old_content_ids)).delete(synchronize_session=False)
        db.query(ContentItem).filter(ContentItem.id.in_(old_content_ids)).delete(synchronize_session=False)
    db.query(AgentRun).filter(AgentRun.campaign_id == c.id).delete(synchronize_session=False)
    c.status = "active"
    c.workflow_status = "running"
    db.commit()


def _persist_result(cid, result, stop_event):
    db = SessionLocal()
    try:
        c = db.get(Campaign, cid)
        if not c:
            return
        if stop_event.is_set():
            c.workflow_status = "stopped"
            c.status = "stopped"
            db.commit()
            return
        c.workflow_status = "awaiting_human_approval"
        c.status = "active"
        c.projected_analytics = json.dumps(result.get("analytics", {}), default=str)
        outputs = {
            "Marketing Requirement Analysis Agent": result.get("campaign_brief"),
            "Audience & Competitor Research Agent": result.get("research"),
            "Campaign Strategy Agent": result.get("strategy"),
            "Content Generation Agent": result.get("content"),
            "Content Review & Brand Compliance Agent": result.get("reviewed_content"),
            "Campaign Analytics Agent": result.get("analytics"),
        }
        for name in AGENT_NAMES:
            db.add(AgentRun(campaign_id=cid, agent_name=name, status="completed",
                            output=json.dumps(outputs.get(name, ""), default=str)))
        for item in result.get("reviewed_content", []):
            ci = ContentItem(
                campaign_id=cid,
                platform=item["platform"],
                content_type=item["content_type"],
                topic=item["topic"],
                body=item["body"],
                review_status=item["review_status"],
                review_notes=item["review_notes"],
                scheduled_date=item["scheduled_date"],
            )
            db.add(ci)
            db.flush()
            db.add(ApprovalStep(content_id=ci.id, status="pending"))
        db.commit()
    finally:
        db.close()


def _worker(cid, stop_event):
    db = SessionLocal()
    try:
        c = db.get(Campaign, cid)
        if not c:
            return
        campaign_brief = brief(c)
    finally:
        db.close()
    try:
        result = orch.run_campaign_cancellable(campaign_brief, stop_event.is_set)
        _persist_result(cid, result, stop_event)
    except WorkflowStopped:
        db = SessionLocal()
        try:
            c = db.get(Campaign, cid)
            if c:
                c.workflow_status = "stopped"
                c.status = "stopped"
                db.commit()
        finally:
            db.close()
    except Exception as exc:
        db = SessionLocal()
        try:
            c = db.get(Campaign, cid)
            if c:
                if stop_event.is_set():
                    c.workflow_status = "stopped"
                    c.status = "stopped"
                else:
                    c.workflow_status = "failed"
                    c.status = "error"
                db.commit()
        finally:
            db.close()
        print(f"Campaign {cid} workflow error: {exc}")
    finally:
        with running_lock:
            running_events.pop(cid, None)


@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": settings.demo_mode}


@app.get("/api/agents")
def agents():
    return {"agents": AGENT_NAMES}


@app.post("/api/campaigns", response_model=CampaignOut)
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
    if not data.platforms:
        raise HTTPException(400, "Select at least one platform.")
    c = Campaign(**data.model_dump(exclude={"platforms"}), platforms=",".join(data.platforms))
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@app.get("/api/campaigns", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).order_by(Campaign.id.desc()).all()


@app.get("/api/campaigns/{cid}", response_model=CampaignOut)
def get_campaign(cid: int, db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    return c


@app.get("/api/campaigns/{cid}/status")
def campaign_status(cid: int, db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    with running_lock:
        running = cid in running_events
    return {"campaign_id": cid, "status": c.status, "workflow_status": c.workflow_status, "running": running}


@app.post("/api/campaigns/{cid}/run")
def run_campaign(cid: int, wait: bool = False, db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    with running_lock:
        if cid in running_events:
            raise HTTPException(409, "Campaign workflow is already running.")
    _prepare_campaign(db, c)
    stop_event = threading.Event()
    with running_lock:
        running_events[cid] = stop_event
    if wait:
        _worker(cid, stop_event)
        return campaign_status(cid, db)
    executor.submit(_worker, cid, stop_event)
    return {"campaign_id": cid, "workflow_status": "running", "agents": AGENT_NAMES}


@app.post("/api/campaigns/{cid}/stop")
def stop_campaign(cid: int, db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    with running_lock:
        event = running_events.get(cid)
    if not event or c.workflow_status != "running":
        raise HTTPException(409, "Campaign workflow is not currently running.")
    event.set()
    c.workflow_status = "stopped"
    c.status = "stopped"
    db.commit()
    return {"campaign_id": cid, "workflow_status": "stopped"}


@app.delete("/api/campaigns/{cid}")
def delete_campaign(cid: int, db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    with running_lock:
        if cid in running_events:
            raise HTTPException(409, "Stop the workflow before deleting this campaign.")
    content_ids = [x.id for x in db.query(ContentItem.id).filter(ContentItem.campaign_id == cid).all()]
    if content_ids:
        db.query(ApprovalStep).filter(ApprovalStep.content_id.in_(content_ids)).delete(synchronize_session=False)
        db.query(ContentItem).filter(ContentItem.id.in_(content_ids)).delete(synchronize_session=False)
    db.query(AgentRun).filter(AgentRun.campaign_id == cid).delete(synchronize_session=False)
    db.delete(c)
    db.commit()
    return {"campaign_id": cid, "status": "deleted"}


@app.get("/api/campaigns/{cid}/research")
def research(cid: int, db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    result = orch.research.run(brief(c))
    return {"sources": result["research"], "personas": result["personas"]}


@app.get("/api/campaigns/{cid}/strategy")
def strategy(cid: int, db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    result = orch.strategy.run({"brief": brief(c)})["strategy"]
    result["total_budget"] = float(c.budget or 0)
    result["budget_allocation_total"] = round(sum(result.get("budget_allocation", {}).values()), 2)
    return result


@app.get("/api/campaigns/{cid}/content")
def content(cid: int, db: Session = Depends(get_db)):
    if not db.get(Campaign, cid):
        raise HTTPException(404, "Campaign not found")
    return [serialize_content(x) for x in db.query(ContentItem).filter(ContentItem.campaign_id == cid).all()]


@app.get("/api/campaigns/{cid}/calendar")
def calendar(cid: int, db: Session = Depends(get_db)):
    if not db.get(Campaign, cid):
        raise HTTPException(404, "Campaign not found")
    return [serialize_content(x) for x in db.query(ContentItem).filter(ContentItem.campaign_id == cid).order_by(ContentItem.scheduled_date).all()]


@app.put("/api/content/{content_id}")
def edit_content(content_id: int, data: ContentUpdate, db: Session = Depends(get_db)):
    x = db.get(ContentItem, content_id)
    if not x:
        raise HTTPException(404, "Content not found")
    if not data.body.strip():
        raise HTTPException(400, "Content cannot be empty.")
    if x.publishing_status == "published":
        raise HTTPException(409, "Published content cannot be edited.")
    x.body = data.body
    x.approval_status = "pending"
    x.publishing_status = "not_published"
    from app.agents.content_review_agent import ContentReviewBrandComplianceAgent
    campaign = db.get(Campaign, x.campaign_id)
    result = ContentReviewBrandComplianceAgent().run({
        "brief": brief(campaign),
        "content": [{"platform": x.platform, "content_type": x.content_type, "topic": x.topic,
                     "body": x.body, "scheduled_date": x.scheduled_date}],
    })
    checked = result["reviewed_content"][0]
    x.review_status = checked["review_status"]
    x.review_notes = checked["review_notes"]
    db.commit()
    return {"status": "updated", **serialize_content(x)}


@app.post("/api/content/{content_id}/approve")
def approve(content_id: int, data: ApprovalRequest, db: Session = Depends(get_db)):
    x = db.get(ContentItem, content_id)
    if not x:
        raise HTTPException(404, "Content not found")
    if x.publishing_status == "published":
        raise HTTPException(409, "Published content is already final.")
    if x.review_status not in ("approved_for_human_review", "passed", "approved"):
        raise HTTPException(409, "Content must pass automated review before human approval.")
    x.approval_status = "approved"
    x.review_notes = data.comment or x.review_notes
    step = db.query(ApprovalStep).filter_by(content_id=content_id).first()
    if step:
        step.status = "approved"
        step.comment = data.comment
    campaign = db.get(Campaign, x.campaign_id)
    db.commit()
    if campaign:
        pending = db.query(ContentItem).filter(ContentItem.campaign_id == campaign.id,
                                               ContentItem.approval_status != "approved").count()
        if pending == 0:
            campaign.workflow_status = "calendar_ready"
            db.commit()
    return {"status": "approved", "content": serialize_content(x)}


@app.post("/api/content/{content_id}/reject")
def reject(content_id: int, data: ApprovalRequest, db: Session = Depends(get_db)):
    x = db.get(ContentItem, content_id)
    if not x:
        raise HTTPException(404, "Content not found")
    if x.publishing_status == "published":
        raise HTTPException(409, "Published content cannot be rejected.")
    x.approval_status = "rejected"
    x.publishing_status = "not_published"
    x.review_notes = data.comment or "Rejected for revision"
    step = db.query(ApprovalStep).filter_by(content_id=content_id).first()
    if step:
        step.status = "rejected"
        step.comment = data.comment
    db.commit()
    return {"status": "rejected", "content": serialize_content(x)}


@app.post("/api/content/{content_id}/regenerate")
def regenerate(content_id: int, db: Session = Depends(get_db)):
    x = db.get(ContentItem, content_id)
    if not x:
        raise HTTPException(404, "Content not found")
    c = db.get(Campaign, x.campaign_id)
    if not c:
        raise HTTPException(404, "Campaign not found")
    if x.publishing_status == "published":
        raise HTTPException(409, "Published content cannot be regenerated.")
    b = brief(c)
    x.body = ContentGenerationAgent()._generate(x.platform, b, x.topic, {})
    x.approval_status = "pending"
    x.publishing_status = "not_published"
    from app.agents.content_review_agent import ContentReviewBrandComplianceAgent
    checked = ContentReviewBrandComplianceAgent().run({
        "brief": b,
        "content": [{"platform": x.platform, "content_type": x.content_type,
                     "topic": x.topic, "body": x.body, "scheduled_date": x.scheduled_date}],
    })["reviewed_content"][0]
    x.review_status = checked["review_status"]
    x.review_notes = checked["review_notes"]
    db.commit()
    return {"status": "regenerated", "content": serialize_content(x)}


@app.post("/api/content/{content_id}/publish")
def publish(content_id: int, db: Session = Depends(get_db)):
    x = db.get(ContentItem, content_id)
    if not x:
        raise HTTPException(404, "Content not found")
    if x.approval_status != "approved":
        raise HTTPException(409, "Publishing is blocked until human approval.")
    if x.review_status not in ("approved_for_human_review", "passed", "approved"):
        raise HTTPException(409, "Publishing is blocked until automated review passes.")
    x.publishing_status = "published"
    db.commit()
    return {"status": "published", "content": serialize_content(x)}


@app.post("/api/campaigns/{cid}/analytics")
def analytics(cid: int, data: dict, db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    if not data.get("observed", False):
        data = dict(data)
        data.update(orch.projected_metrics(brief(c)))
        data["observed"] = False
    result = CampaignAnalyticsAgent().run(data)
    if result.get("observed"):
        c.observed_analytics = json.dumps(result)
    else:
        c.projected_analytics = json.dumps(result)
    db.commit()
    return result


@app.post("/api/campaigns/{cid}/analytics/upload")
def analytics_upload(cid: int, file: UploadFile = File(...), targets: str = Form("{}"), db: Session = Depends(get_db)):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    try:
        text = file.file.read().decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must be UTF-8 encoded")
    if not rows:
        raise HTTPException(400, "CSV contains no data rows")
    keys = ["impressions", "engagements", "clicks", "conversions", "spending", "leads"]
    missing = [k for k in keys if k not in (rows[0] or {})]
    if missing:
        raise HTTPException(400, f"CSV is missing required columns: {', '.join(missing)}")
    try:
        totals = {k: sum(float(r.get(k, 0) or 0) for r in rows) for k in keys}
    except (TypeError, ValueError):
        raise HTTPException(400, "CSV contains non-numeric KPI values")
    if any(v < 0 for v in totals.values()):
        raise HTTPException(400, "CSV KPI values cannot be negative")
    if totals["engagements"] > totals["impressions"] or totals["clicks"] > totals["impressions"] or totals["conversions"] > totals["clicks"]:
        raise HTTPException(400, "CSV KPI relationships are invalid: engagements/clicks cannot exceed impressions and conversions cannot exceed clicks")
    try:
        parsed_targets = json.loads(targets or "{}")
        if not isinstance(parsed_targets, dict):
            raise ValueError
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(400, "Invalid analytics targets.")
    totals["observed"] = True
    totals["targets"] = parsed_targets
    result = CampaignAnalyticsAgent().run(totals)
    c.observed_analytics = json.dumps(result)
    db.commit()
    return result


def report_data(cid, db):
    c = db.get(Campaign, cid)
    if not c:
        raise HTTPException(404, "Campaign not found")
    items = db.query(ContentItem).filter_by(campaign_id=cid).all()
    b = brief(c)
    runs = db.query(AgentRun).filter_by(campaign_id=cid).all()
    outputs = {r.agent_name: r.output for r in runs}
    try:
        strat = json.loads(outputs.get("Campaign Strategy Agent", "{}"))
    except Exception:
        strat = orch.strategy.run({"brief": b})["strategy"]
    try:
        research_data = json.loads(outputs.get("Audience & Competitor Research Agent", "[]"))
    except Exception:
        research_data = orch.research.run(b)["research"]
    analytics_data = {}
    if c.observed_analytics:
        try:
            analytics_data = json.loads(c.observed_analytics)
        except Exception:
            analytics_data = {}
    if not analytics_data and c.projected_analytics:
        try:
            analytics_data = json.loads(c.projected_analytics)
        except Exception:
            analytics_data = {}
    if not analytics_data:
        analytics_data = CampaignAnalyticsAgent().run(orch.projected_metrics(b))
    return c, items, strat, research_data, analytics_data


@app.get("/api/campaigns/{cid}/export/csv")
def export_csv(cid: int, db: Session = Depends(get_db)):
    _, items, _, _, _ = report_data(cid, db)
    return Response(csv_bytes(items), media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=campaign-{cid}.csv"})


@app.get("/api/campaigns/{cid}/export/pdf")
def export_pdf(cid: int, db: Session = Depends(get_db)):
    c, items, strat, research_data, analytics_data = report_data(cid, db)
    return Response(pdf_bytes(c, items, strat, research_data, analytics_data), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=campaign-{cid}.pdf"})


@app.get("/api/campaigns/{cid}/report")
def report(cid: int, db: Session = Depends(get_db)):
    c, items, strat, research_data, analytics_data = report_data(cid, db)
    return {
        "campaign": brief(c), "strategy": strat, "research": research_data,
        "analytics": analytics_data,
        "content_calendar": [serialize_content(x) for x in items],
        "approval": {
            "approved": sum(x.approval_status == "approved" for x in items),
            "pending": sum(x.approval_status != "approved" for x in items),
        },
        "workflow_status": c.workflow_status,
    }
