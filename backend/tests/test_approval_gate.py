from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_publish_requires_human_approval():
    payload={"product_name":"Approval Gate Demo","description":"Test product","target_audience":"Test buyers","objective":"Generate leads","budget":1000,"duration_days":7,"platforms":["LinkedIn"],"brand_tone":"Professional","brand_guidelines":"Avoid unsupported claims."}
    c=client.post('/api/campaigns',json=payload).json()
    client.post(f"/api/campaigns/{c['id']}/run")
    item=client.get(f"/api/campaigns/{c['id']}/content").json()[0]
    r=client.post(f"/api/content/{item['id']}/publish")
    assert r.status_code==409
    client.post(f"/api/content/{item['id']}/approve",json={"comment":"Approved by reviewer"})
    r=client.post(f"/api/content/{item['id']}/publish")
    assert r.status_code==200


def test_rejected_content_cannot_be_approved():
    payload={"product_name":"Review Gate Demo","description":"Test product","target_audience":"Test buyers","objective":"Generate leads","budget":1000,"duration_days":7,"platforms":["LinkedIn"],"brand_tone":"Professional","brand_guidelines":"Avoid unsupported claims."}
    c=client.post('/api/campaigns',json=payload).json()
    client.post(f"/api/campaigns/{c['id']}/run")
    item=client.get(f"/api/campaigns/{c['id']}/content").json()[0]
    # Force an invalid review state through the test database and verify the API gate.
    from app.core.database import SessionLocal
    from app.models import ContentItem
    db=SessionLocal(); obj=db.get(ContentItem,item['id']); obj.review_status='rejected'; db.commit(); db.close()
    r=client.post(f"/api/content/{item['id']}/approve",json={"comment":"Trying to bypass review"})
    assert r.status_code==409
