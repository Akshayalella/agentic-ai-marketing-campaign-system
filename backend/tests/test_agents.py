from app.agents.analytics_agent import CampaignAnalyticsAgent
def test_kpis():
 r=CampaignAnalyticsAgent().run({'impressions':1000,'engagements':100,'clicks':50,'conversions':10,'spending':500,'leads':5,'observed':True})
 assert r['engagement_rate']==10 and r['ctr']==5 and r['conversion_rate']==20 and r['cost_per_lead']==100
