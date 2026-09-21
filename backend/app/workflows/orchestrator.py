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

    PLATFORM_ASSUMPTIONS = {
        "LinkedIn": {"engagement": 0.055, "ctr": 0.028, "conversion": 0.040, "cpm": 650},
        "Instagram": {"engagement": 0.060, "ctr": 0.030, "conversion": 0.035, "cpm": 450},
        "Email": {"engagement": 0.085, "ctr": 0.045, "conversion": 0.060, "cpm": 250},
        "Facebook": {"engagement": 0.050, "ctr": 0.022, "conversion": 0.030, "cpm": 500},
        "X": {"engagement": 0.045, "ctr": 0.020, "conversion": 0.025, "cpm": 550},
        "YouTube": {"engagement": 0.050, "ctr": 0.025, "conversion": 0.028, "cpm": 600},
    }

    @classmethod
    def projected_metrics(cls, campaign_brief):
        """Create transparent planning estimates from campaign inputs.

        Projected metrics are not observed performance. Budget, selected platforms and
        duration influence the estimates, with modest diminishing returns as spend grows.
        """
        import math

        budget=max(float(campaign_brief.get("budget",0) or 0),0.0)
        platforms=list(dict.fromkeys(campaign_brief.get("platforms",[]) or []))
        if not platforms:
            platforms=["LinkedIn"]
        duration=max(float(campaign_brief.get("duration_days",30) or 30),1.0)

        assumptions=[cls.PLATFORM_ASSUMPTIONS.get(p, {"engagement":0.05,"ctr":0.025,"conversion":0.03,"cpm":500}) for p in platforms]
        # Strategy-style platform weights: LinkedIn > Instagram > Email, normalized to selection.
        weights={"LinkedIn":0.40,"Instagram":0.30,"Email":0.20,"Facebook":0.10,"X":0.10,"YouTube":0.20}
        raw=[weights.get(p,1/len(platforms)) for p in platforms]
        total=sum(raw) or 1.0
        raw=[w/total for w in raw]

        def weighted(key):
            return sum(w*a[key] for w,a in zip(raw,assumptions))

        # More budget improves reach and conversion efficiency, but only gradually.
        budget_scale=1.0 + min(0.25, 0.18*math.log10(max(budget,1000)/5000.0 + 1.0))
        duration_scale=1.0 + min(0.08, max(0.0,duration-30)/365.0)
        engagement_rate=min(12.0, weighted("engagement")*100*budget_scale)
        ctr=min(8.0, weighted("ctr")*100*(0.98+0.02*budget_scale))
        conversion_rate=min(12.0, weighted("conversion")*100*(0.97+0.03*budget_scale)*duration_scale)
        blended_cpm=max(50.0,weighted("cpm"))
        impressions=max(1,round((budget/blended_cpm)*1000)) if budget else 0
        engagements=round(impressions*engagement_rate/100)
        clicks=round(impressions*ctr/100)
        conversions=max(0.0, clicks*conversion_rate/100)
        leads=max(0.1, conversions*0.90) if conversions else 0

        return {
            "impressions":impressions,
            "engagements":engagements,
            "clicks":clicks,
            "conversions":conversions,
            "spending":round(budget,2),
            "leads":leads,
            "observed":False,
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
                metrics = self.projected_metrics(s["campaign_brief"])
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
        metrics = self.projected_metrics(brief)
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
