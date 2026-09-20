from app.agents.requirement_analysis_agent import RequirementAnalysisAgent
from app.agents.audience_research_agent import AudienceCompetitorResearchAgent
from app.agents.strategy_agent import CampaignStrategyAgent
from app.agents.content_generation_agent import ContentGenerationAgent
from app.agents.content_review_agent import ContentReviewBrandComplianceAgent
from app.agents.analytics_agent import CampaignAnalyticsAgent
from app.services.research_provider import DemoResearchProvider

def brief(**overrides):
    b={"product_name":"AI Resume Screening Platform","description":"Resume parsing and matching",
       "target_audience":"HR Managers","objective":"Generate qualified leads","budget":50000,
       "duration_days":30,"platforms":["LinkedIn","Email","Instagram"],"brand_tone":"Professional",
       "brand_guidelines":"Avoid unsupported claims."}
    b.update(overrides); return b

def test_tc01_product_launch():
    b=brief()
    s=RequirementAnalysisAgent().run(b)
    assert s["campaign_brief"]["product_name"]=="AI Resume Screening Platform"
    strategy=CampaignStrategyAgent().run({"brief":s["campaign_brief"]})["strategy"]
    assert strategy["timeline_days"]==30 and strategy["budget_allocation"]

def test_tc02_linkedin_only():
    b=brief(platforms=["LinkedIn"])
    out=ContentGenerationAgent().run({"brief":b})["content"]
    assert out and all(x["platform"]=="LinkedIn" for x in out)

def test_tc03_limited_budget():
    b=brief(budget=1000)
    strategy=CampaignStrategyAgent().run({"brief":b})["strategy"]
    assert sum(strategy["budget_allocation"].values())==1000

def test_tc04_unsupported_claim():
    b=brief()
    out=ContentReviewBrandComplianceAgent().run({"brief":b,"content":[
        {"platform":"LinkedIn","content_type":"post","topic":"claim",
         "body":"Our product is 100% guaranteed and #1 in the world.","scheduled_date":"2026-09-19"}
    ]})["reviewed_content"][0]
    assert out["review_status"]=="rejected"

def test_tc05_performance_kpis():
    r=CampaignAnalyticsAgent().run({"impressions":1000,"engagements":100,"clicks":50,
        "conversions":10,"spending":500,"leads":5,"observed":True})
    assert r["engagement_rate"]==10
    assert r["ctr"]==5
    assert r["conversion_rate"]==20
    assert r["cost_per_lead"]==100

def test_research_sources():
    result=AudienceCompetitorResearchAgent(DemoResearchProvider()).run(brief())
    assert result["research"] and all("url" in x and "source_type" in x for x in result["research"])

def test_strategy_has_required_sections():
    strategy=CampaignStrategyAgent().run({"brief":brief()})["strategy"]
    for key in ["objectives","audience_segments","channels","content_strategy","timeline_days","budget_allocation","kpis"]:
        assert key in strategy
    assert round(sum(strategy["budget_allocation"].values()),2)==50000


def test_analytics_rejects_invalid_csv(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    payload={"product_name":"CSV Validation Demo","budget":1000,"platforms":["LinkedIn"]}
    c=client.post('/api/campaigns',json=payload).json()
    bad=tmp_path/'bad.csv'; bad.write_text('impressions,engagements,clicks,conversions,spending,leads\n100,120,50,10,500,5\n')
    with bad.open('rb') as fh:
        r=client.post(f"/api/campaigns/{c['id']}/analytics/upload",files={"file":("bad.csv",fh,"text/csv")})
    assert r.status_code==400


def test_analytics_targets_survive_csv_upload(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    c = client.post('/api/campaigns', json={"product_name": "Analytics Target Demo", "budget": 1000, "platforms": ["LinkedIn"]}).json()
    csv_path = tmp_path / 'performance.csv'
    csv_path.write_text('impressions,engagements,clicks,conversions,spending,leads\n10000,800,500,75,12000,60\n')
    with csv_path.open('rb') as fh:
        response = client.post(
            f"/api/campaigns/{c['id']}/analytics/upload",
            files={"file": ("performance.csv", fh, "text/csv")},
            data={"targets": '{"engagement_rate":5,"ctr":2,"conversion_rate":1,"cost_per_lead":500}'},
        )
    assert response.status_code == 200
    result = response.json()
    assert result["observed"] is True
    assert result["performance_score"] > 0
    assert result["target_comparison"]["engagement_rate"]["status"] == "meets_target"
