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


def test_new_campaign_is_not_active_until_run_starts():
    c = client.post("/api/campaigns", json=payload("Lifecycle Demo")).json()
    assert c["status"] == "draft"
    assert c["workflow_status"] == "not_started"
    client.post(f"/api/campaigns/{c['id']}/run?wait=true")
    refreshed = client.get(f"/api/campaigns/{c['id']}").json()
    assert refreshed["status"] == "active"
    assert refreshed["workflow_status"] == "awaiting_human_approval"


def test_run_immediately_marks_campaign_active_and_workflow_running(monkeypatch):
    c = client.post("/api/campaigns", json=payload("Run State Demo")).json()
    cid = c["id"]
    release = threading.Event()

    def blocked_run(brief, stop_check):
        while not release.is_set():
            if stop_check():
                raise WorkflowStopped("Workflow stopped by user")
            time.sleep(0.01)
        return {"analytics": {}, "reviewed_content": []}

    monkeypatch.setattr("app.main.orch.run_campaign_cancellable", blocked_run)
    result = client.post(f"/api/campaigns/{cid}/run")
    assert result.status_code == 200
    assert result.json()["workflow_status"] == "running"
    status = client.get(f"/api/campaigns/{cid}/status").json()
    assert status["status"] == "active"
    assert status["workflow_status"] == "running"
    assert status["running"] is True
    release.set()
    deadline = time.time() + 2
    while time.time() < deadline:
        status = client.get(f"/api/campaigns/{cid}/status").json()
        if status["running"] is False:
            break
        time.sleep(0.03)


def test_stop_unused_campaign_is_allowed():
    c = client.post("/api/campaigns", json=payload("Unused Stop Demo")).json()
    cid = c["id"]
    result = client.post(f"/api/campaigns/{cid}/stop")
    assert result.status_code == 200
    body = result.json()
    assert body["workflow_status"] == "stopped"
    assert body["status"] == "stopped"
    assert client.get(f"/api/campaigns/{cid}/status").json()["running"] is False


def test_campaign_list_uses_user_facing_creation_order():
    first = client.post("/api/campaigns", json=payload("First List Demo")).json()
    second = client.post("/api/campaigns", json=payload("Second List Demo")).json()
    listed = client.get("/api/campaigns").json()
    ids = [item["id"] for item in listed if item["id"] in {first["id"], second["id"]}]
    assert ids == [first["id"], second["id"]]
