class CampaignAnalyticsAgent:
    name="Campaign Analytics Agent"

    def run(self, data):
        imp=float(data.get("impressions",0) or 0)
        eng=float(data.get("engagements",0) or 0)
        clicks=float(data.get("clicks",0) or 0)
        conv=float(data.get("conversions",0) or 0)
        spend=float(data.get("spending",0) or 0)
        leads=float(data.get("leads",0) or 0)

        result={
            "observed":bool(data.get("observed",False)),
            "engagement_rate":eng/imp*100 if imp else 0,
            "ctr":clicks/imp*100 if imp else 0,
            "conversion_rate":conv/clicks*100 if clicks else 0,
            "cost_per_lead":spend/leads if leads else 0,
            "spending":spend,
        }

        # Optional target comparison. Targets are percentages for rate metrics
        # and currency values for CPL/spending.
        targets=data.get("targets") or {}
        if targets:
            result["target_comparison"]={}
            for metric in ("engagement_rate","ctr","conversion_rate","cost_per_lead","spending"):
                if metric in targets and targets[metric] is not None:
                    actual=result[metric]
                    target=float(targets[metric])
                    if metric in {"cost_per_lead","spending"}:
                        direction="better" if actual <= target else "above_target"
                    else:
                        direction="better" if actual >= target else "below_target"
                    result["target_comparison"][metric]={
                        "actual":actual,
                        "target":target,
                        "status":direction,
                    }

        # Optional trend comparison against a previous period.
        previous=data.get("previous") or {}
        if previous:
            result["trends"]={}
            for metric in ("engagement_rate","ctr","conversion_rate","cost_per_lead","spending"):
                if metric in previous and previous[metric] is not None:
                    old=float(previous[metric])
                    new=result[metric]
                    result["trends"][metric]={
                        "previous":old,
                        "current":new,
                        "change":new-old,
                        "change_percent":((new-old)/old*100) if old else None,
                    }

        # Actionable suggestions based on the observed/projected metrics.
        suggestions=[]
        if imp and result["ctr"] < 1:
            suggestions.append("Review creative and calls to action because CTR is below 1%.")
        if clicks and result["conversion_rate"] < 2:
            suggestions.append("Review landing-page relevance and conversion flow because conversion rate is below 2%.")
        if leads and result["cost_per_lead"] > 0:
            suggestions.append("Monitor cost per lead against the campaign target and shift budget toward efficient channels when supported by observed data.")
        if not suggestions:
            suggestions.append("Continue monitoring observed metrics and compare them with campaign targets before changing budget allocation.")
        result["improvement_suggestions"]=suggestions
        return result
