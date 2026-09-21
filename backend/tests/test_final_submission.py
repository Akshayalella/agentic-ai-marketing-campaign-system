from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_strategy_api_exposes_total_and_allocation_total():
    campaign = client.post(
        "/api/campaigns",
        json={"product_name": "Budget Demo", "budget": 5000, "platforms": ["LinkedIn", "Instagram", "Email"]},
    ).json()
    result = client.get(f"/api/campaigns/{campaign['id']}/strategy")
    assert result.status_code == 200
    data = result.json()
    assert data["total_budget"] == 5000
    assert data["budget_allocation_total"] == 5000


def test_campaign_run_creates_exactly_one_item_per_selected_platform():
    campaign = client.post(
        "/api/campaigns",
        json={"product_name": "Platform Demo", "budget": 5000, "platforms": ["LinkedIn", "Instagram", "Email"]},
    ).json()
    result = client.post(f"/api/campaigns/{campaign['id']}/run?wait=true")
    assert result.status_code == 200
    items = client.get(f"/api/campaigns/{campaign['id']}/content").json()
    assert len(items) == 3
    assert {item["platform"] for item in items} == {"LinkedIn", "Instagram", "Email"}


def test_projected_analytics_api_uses_campaign_budget():
    small = client.post(
        "/api/campaigns",
        json={"product_name": "Small Budget", "budget": 5000, "platforms": ["LinkedIn"]},
    ).json()
    large = client.post(
        "/api/campaigns",
        json={"product_name": "Large Budget", "budget": 50000, "platforms": ["LinkedIn"]},
    ).json()
    small_result = client.post(f"/api/campaigns/{small['id']}/analytics", json={"observed": False}).json()
    large_result = client.post(f"/api/campaigns/{large['id']}/analytics", json={"observed": False}).json()
    assert small_result["spending"] == 5000
    assert large_result["spending"] == 50000
    assert small_result["engagement_rate"] != large_result["engagement_rate"]
