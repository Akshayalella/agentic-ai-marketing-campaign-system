from app.agents import (
    RequirementAnalysisAgent, AudienceCompetitorResearchAgent,
    CampaignStrategyAgent, ContentGenerationAgent,
    ContentReviewBrandComplianceAgent, CampaignAnalyticsAgent,
)
from app.services.research_provider import DemoResearchProvider, WebResearchProvider


class WorkflowStopped(Exception):
    """Raised when a user requests cancellation between workflow stages."""


class CampaignOrchestrator:
    """Six-agent shared-state workflow with optional LangGraph orchestration."""

    PROJECTED_METRICS = {
        "impressions": 10000,
        "engagements": 700,
        "clicks": 400,
        "conversions": 45,
        "spending": 12000,
        "leads": 45,
        "observed": False,
    }

    def __init__(self, research_provider=None):
        from app.core.config import settings

        provider = research_provider or (
            WebResearchProvider()
            if settings.research_provider == "web"
            else DemoResearchProvider()
        )
        self.req = RequirementAnalysisAgent()
        self.research = AudienceCompetitorResearchAgent(provider)
        self.strategy = CampaignStrategyAgent()
        self.content = ContentGenerationAgent()
        self.review = ContentReviewBrandComplianceAgent()
        self.analytics = CampaignAnalyticsAgent()
        self.graph = self._build_graph()

    def _guard(self, stop_check):
        if stop_check and stop_check():
            raise WorkflowStopped("Workflow stopped by user")

    def _build_graph(self, stop_check=None):
        try:
            from langgraph.graph import StateGraph, START, END
            from typing import TypedDict

            class State(TypedDict, total=False):
                brief_input: dict
                brief: dict
                campaign_brief: dict
                research: list
                personas: list
                strategy: dict
                content: list
                reviewed_content: list
                analytics: dict
                workflow_status: str

            def requirements(s):
                self._guard(stop_check)
                return self.req.run(s["brief_input"])

            def research(s):
                self._guard(stop_check)
                return self.research.run(s["campaign_brief"])

            def strategy(s):
                self._guard(stop_check)
                return self.strategy.run({"brief": s["campaign_brief"], **s})

            def content(s):
                self._guard(stop_check)
                return self.content.run({"brief": s["campaign_brief"], **s})

            def review(s):
                self._guard(stop_check)
                return self.review.run({"brief": s["campaign_brief"], **s})

            def analytics(s):
                self._guard(stop_check)
                metrics = dict(self.PROJECTED_METRICS)
                metrics["spending"] = float(s["campaign_brief"].get("budget", 0) or 0)
                return {"analytics": self.analytics.run(metrics)}

            g = StateGraph(State)
            g.add_node("requirements", requirements)
            g.add_node("research", research)
            g.add_node("strategy", strategy)
            g.add_node("content", content)
            g.add_node("review", review)
            g.add_node("analytics", analytics)
            g.add_edge(START, "requirements")
            g.add_edge("requirements", "research")
            g.add_edge("research", "strategy")
            g.add_edge("strategy", "content")
            g.add_edge("content", "review")
            g.add_edge("review", "analytics")
            g.add_edge("analytics", END)
            return g.compile()
        except Exception:
            return None

    def _sequential(self, brief, stop_check=None):
        state = {"brief_input": brief}
        self._guard(stop_check)
        state.update(self.req.run(brief))
        state["brief"] = state["campaign_brief"]
        self._guard(stop_check)
        state.update(self.research.run(state["brief"]))
        self._guard(stop_check)
        state.update(self.strategy.run(state))
        self._guard(stop_check)
        state.update(self.content.run(state))
        self._guard(stop_check)
        state.update(self.review.run(state))
        self._guard(stop_check)
        metrics = dict(self.PROJECTED_METRICS)
        metrics["spending"] = float(brief.get("budget", 0) or 0)
        state["analytics"] = self.analytics.run(metrics)
        self._guard(stop_check)
        return state

    def run_campaign(self, brief):
        if self.graph:
            state = self.graph.invoke({"brief_input": brief})
        else:
            state = self._sequential(brief)
        state["workflow_status"] = "awaiting_human_approval"
        return state

    def run_campaign_cancellable(self, brief, stop_check):
        """Run the same six-agent graph with stop checks between stages."""
        graph = self._build_graph(stop_check)
        if graph:
            state = graph.invoke({"brief_input": brief})
        else:
            state = self._sequential(brief, stop_check)
        state["workflow_status"] = "awaiting_human_approval"
        return state
