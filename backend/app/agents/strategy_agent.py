class CampaignStrategyAgent:
    name="Campaign Strategy Agent"

    def run(self,state):
        b=state["brief"]; budget=float(b.get("budget",0) or 0); platforms=b.get("platforms",[]) or []
        weights={"LinkedIn":0.40,"Instagram":0.30,"Email":0.20,"Facebook":0.10,"X":0.10,"YouTube":0.20}
        raw={p:weights.get(p,1/max(len(platforms),1)) for p in platforms}
        total=sum(raw.values()) or 1
        allocation={p:round(budget*v/total,2) for p,v in raw.items()}
        # Correct rounding drift so the allocation always equals the requested budget.
        if allocation:
            first=next(iter(allocation)); allocation[first]=round(allocation[first]+budget-sum(allocation.values()),2)
        duration=max(1,int(b.get("duration_days",30) or 30))
        awareness=max(1, round(duration*0.25))
        consideration=max(1, round(duration*0.45))
        if awareness + consideration > duration:
            consideration=max(0, duration-awareness)
        conversion=duration-awareness-consideration
        if conversion < 0:
            conversion=0
            consideration=max(0, duration-awareness)
        audience=b.get("target_audience","target customers")
        objective=b.get("objective","achieve the campaign objective")
        return {"strategy":{
            "theme":f"Simplify {b.get('product_name','your workflow')} with AI",
            "objectives":[objective],
            "audience_segments":[
                {"name":"Primary decision makers","description":audience},
                {"name":"Evaluation influencers","description":f"People who research and recommend solutions for {audience}."}
            ],
            "channels":platforms,
            "content_strategy":{
                "LinkedIn":"Educational thought leadership, product value and proof points",
                "Email":"Problem-solution sequence with CTA and follow-up",
                "Instagram":"Short feature/value stories and visual hooks"
            },
            "posting_cadence":{p:{"LinkedIn":3,"Email":1,"Instagram":2}.get(p,1) for p in platforms},
            "budget_allocation":allocation,
            "timeline_days":duration,
            "timeline_phases":[
                {"phase":"Awareness","days":awareness,"focus":"Problem education and audience reach"},
                {"phase":"Consideration","days":consideration,"focus":"Features, differentiation and trust"},
                {"phase":"Conversion","days":conversion,"focus":"CTA, follow-up and lead conversion"}
            ],
            "kpis":["Engagement rate","CTR","Conversion rate","Cost per lead"],
            "success_criteria":["Approved platform-specific content","Measurable lead generation","Observed metrics separated from projections"]
        },"status":"completed"}
