from app.agents.analytics_agent import CampaignAnalyticsAgent


def test_projected_and_observed_scores_can_differ():
    agent = CampaignAnalyticsAgent()
    projected = agent.run({
        "impressions": 10000, "engagements": 700, "clicks": 400,
        "conversions": 45, "spending": 12000, "leads": 45, "observed": False,
    })
    observed = agent.run({
        "impressions": 10000, "engagements": 800, "clicks": 500,
        "conversions": 75, "spending": 12000, "leads": 60, "observed": True,
    })
    assert projected["performance_score"] != observed["performance_score"]
    assert projected["performance_score"] < observed["performance_score"]
    assert projected["observed"] is False
    assert observed["observed"] is True


def test_targets_do_not_make_performance_score_identical():
    agent = CampaignAnalyticsAgent()
    projected = agent.run({
        "impressions": 10000, "engagements": 700, "clicks": 400,
        "conversions": 45, "spending": 12000, "leads": 45, "observed": False,
        "targets": {"engagement_rate": 5, "ctr": 2, "conversion_rate": 1, "cost_per_lead": 500},
    })
    observed = agent.run({
        "impressions": 10000, "engagements": 800, "clicks": 500,
        "conversions": 75, "spending": 12000, "leads": 60, "observed": True,
        "targets": {"engagement_rate": 5, "ctr": 2, "conversion_rate": 1, "cost_per_lead": 500},
    })
    assert projected["performance_score"] != observed["performance_score"]
