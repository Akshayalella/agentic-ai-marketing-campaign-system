import threading
import time

from fastapi.testclient import TestClient

from app.main import app, running_events, running_lock
from app.core.database import SessionLocal
from app.models import Campaign
from app.workflows.orchestrator import WorkflowStopped

client = TestClient(app)


def payload(name="Controls Demo"):
    return {
        "product_name": name,
        "description": "A test product",
        "target_audience": "Test buyers",
        "objective": "Generate qualified leads",
        "budget": 5000,
        "duration_days": 7,
        "platforms": ["LinkedIn"],
        "brand_tone": "Professional",
        "brand_guidelines": "Avoid unsupported claims.",
    }


def test_campaign_run_wait_status_and_content():
    c = client.post("/api/campaigns", json=payload()).json()
    result = client.post(f"/api/campaigns/{c['id']}/run?wait=true")
    assert result.status_code == 200
    assert result.json()["workflow_status"] == "awaiting_human_approval"
    assert client.get(f"/api/campaigns/{c['id']}/content").json()


def test_async_run_can_be_stopped(monkeypatch):
    c = client.post("/api/campaigns", json=payload("Async Stop Demo")).json()
    cid = c["id"]

    def slow_run(brief, stop_check):
        while not stop_check():
            time.sleep(0.02)
        raise WorkflowStopped("Workflow stopped by user")

    monkeypatch.setattr("app.main.orch.run_campaign_cancellable", slow_run)
    start = client.post(f"/api/campaigns/{cid}/run")
    assert start.status_code == 200
    time.sleep(0.05)
    result = client.post(f"/api/campaigns/{cid}/stop")
    assert result.status_code == 200
    assert result.json()["workflow_status"] == "stopped"
    deadline = time.time() + 2
    while time.time() < deadline:
        status = client.get(f"/api/campaigns/{cid}/status").json()
        if status["workflow_status"] == "stopped" and not status["running"]:
            break
        time.sleep(0.03)
    assert status["workflow_status"] == "stopped"
    assert status["running"] is False


def test_stop_endpoint_changes_running_campaign_to_stopped():
    c = client.post("/api/campaigns", json=payload("Stop Demo")).json()
    cid = c["id"]
    db = SessionLocal()
    obj = db.get(Campaign, cid)
    obj.status = "active"
    obj.workflow_status = "running"
    db.commit()
    db.close()
    event = threading.Event()
    with running_lock:
        running_events[cid] = event
    result = client.post(f"/api/campaigns/{cid}/stop")
    assert result.status_code == 200
    assert result.json()["workflow_status"] == "stopped"
    with running_lock:
        running_events.pop(cid, None)


def test_delete_campaign_removes_it_and_dependents():
    c = client.post("/api/campaigns", json=payload("Delete Demo")).json()
    cid = c["id"]
    client.post(f"/api/campaigns/{cid}/run?wait=true")
    result = client.delete(f"/api/campaigns/{cid}")
    assert result.status_code == 200
    assert client.get(f"/api/campaigns/{cid}").status_code == 404


def test_cannot_delete_while_running():
    c = client.post("/api/campaigns", json=payload("Delete Running Demo")).json()
    cid = c["id"]
    db = SessionLocal()
    obj = db.get(Campaign, cid)
    obj.status = "active"
    obj.workflow_status = "running"
    db.commit()
    db.close()
    with running_lock:
        running_events[cid] = threading.Event()
    result = client.delete(f"/api/campaigns/{cid}")
    assert result.status_code == 409
    with running_lock:
        running_events.pop(cid, None)
