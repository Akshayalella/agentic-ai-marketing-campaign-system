from app.agents.analytics_agent import CampaignAnalyticsAgent
def test_kpis():
 r=CampaignAnalyticsAgent().run({'impressions':1000,'engagements':100,'clicks':50,'conversions':10,'spending':500,'leads':5,'observed':True})
 assert r['engagement_rate']==10 and r['ctr']==5 and r['conversion_rate']==20 and r['cost_per_lead']==100


def test_analytics_targets_trends_and_suggestions():
 r=CampaignAnalyticsAgent().run({
   "impressions":1000,"engagements":50,"clicks":5,"conversions":0,
   "spending":500,"leads":2,"observed":True,
   "targets":{"engagement_rate":8,"ctr":2,"conversion_rate":2,"cost_per_lead":200},
   "previous":{"engagement_rate":8,"ctr":1,"conversion_rate":3,"cost_per_lead":150}
 })
 assert "target_comparison" in r
 assert r["target_comparison"]["engagement_rate"]["status"]=="below_target"
 assert "trends" in r and "ctr" in r["trends"]
 assert r["improvement_suggestions"]
