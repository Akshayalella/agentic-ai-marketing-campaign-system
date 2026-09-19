class CampaignAnalyticsAgent:
    name="Campaign Analytics Agent"
    def run(self,data):
        imp=float(data.get("impressions",0)); eng=float(data.get("engagements",0)); clicks=float(data.get("clicks",0)); conv=float(data.get("conversions",0)); spend=float(data.get("spending",0)); leads=float(data.get("leads",0))
        return {"observed":bool(data.get("observed",False)),"engagement_rate":eng/imp*100 if imp else 0,"ctr":clicks/imp*100 if imp else 0,"conversion_rate":conv/clicks*100 if clicks else 0,"cost_per_lead":spend/leads if leads else 0,"spending":spend}
