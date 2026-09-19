from app.agents import (
    RequirementAnalysisAgent, AudienceCompetitorResearchAgent,
    CampaignStrategyAgent, ContentGenerationAgent,
    ContentReviewBrandComplianceAgent, CampaignAnalyticsAgent,
)
from app.services.research_provider import DemoResearchProvider, WebResearchProvider

class CampaignOrchestrator:
    """Six-agent shared-state workflow with LangGraph orchestration when available.

    A small deterministic fallback keeps local/demo execution available if LangGraph
    is not installed.
    """
    def __init__(self, research_provider=None):
        from app.core.config import settings
        provider = research_provider or (WebResearchProvider() if settings.research_provider == "web" else DemoResearchProvider())
        self.req = RequirementAnalysisAgent()
        self.research = AudienceCompetitorResearchAgent(provider)
        self.strategy = CampaignStrategyAgent()
        self.content = ContentGenerationAgent()
        self.review = ContentReviewBrandComplianceAgent()
        self.analytics = CampaignAnalyticsAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        try:
            from langgraph.graph import StateGraph, START, END
            from typing import TypedDict, Any
            class State(TypedDict, total=False):
                brief_input: dict; brief: dict; campaign_brief: dict; research: list; personas: list
                strategy: dict; content: list; reviewed_content: list; analytics: dict; workflow_status: str
            g=StateGraph(State)
            g.add_node("requirements", lambda s: self.req.run(s["brief_input"]))
            g.add_node("research", lambda s: self.research.run(s["campaign_brief"]))
            g.add_node("strategy", lambda s: self.strategy.run({"brief":s["campaign_brief"], **s}))
            g.add_node("content", lambda s: self.content.run({"brief":s["campaign_brief"], **s}))
            g.add_node("review", lambda s: self.review.run({"brief":s["campaign_brief"], **s}))
            g.add_node("analytics", lambda s: {"analytics": self.analytics.run({
                "impressions":10000,"engagements":700,"clicks":450,"conversions":45,
                "spending":float(s["campaign_brief"].get("budget",0)),"leads":45,"observed":False
            })})
            g.add_edge(START,"requirements"); g.add_edge("requirements","research"); g.add_edge("research","strategy")
            g.add_edge("strategy","content"); g.add_edge("content","review"); g.add_edge("review","analytics"); g.add_edge("analytics",END)
            return g.compile()
        except Exception:
            return None

    def run_campaign(self, brief):
        if self.graph:
            state=self.graph.invoke({"brief_input":brief})
        else:
            state={"brief_input":brief}
            state.update(self.req.run(brief)); state["brief"]=state["campaign_brief"]
            state.update(self.research.run(state["brief"])); state.update(self.strategy.run(state))
            state.update(self.content.run(state)); state.update(self.review.run(state))
            state["analytics"]=self.analytics.run({"impressions":10000,"engagements":700,"clicks":450,
                "conversions":45,"spending":float(brief.get("budget",0)),"leads":45,"observed":False})
        state["workflow_status"]="awaiting_human_approval"
        return state
