class AudienceCompetitorResearchAgent:
    name="Audience & Competitor Research Agent"
    def __init__(self,research): self.research=research
    def run(self,brief):
        q=f"{brief.get('product_name')} {brief.get('target_audience')} competitors"
        return {"research":self.research.search(q),"personas":[{"name":"Primary buyer","description":brief.get("target_audience","Target customer"),"verified":False}],"status":"completed"}
