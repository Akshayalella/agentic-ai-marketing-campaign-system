class RequirementAnalysisAgent:
    name="Marketing Requirement Analysis Agent"
    def run(self,brief):
        return {"campaign_brief":{**brief,"required_platforms":brief.get("platforms",[])},"status":"completed"}
