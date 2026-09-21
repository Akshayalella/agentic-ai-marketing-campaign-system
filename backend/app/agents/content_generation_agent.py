from datetime import date, timedelta
from app.services.llm_provider import get_llm

class ContentGenerationAgent:
    name="Content Generation Agent"

    def __init__(self,llm=None):
        self.llm=llm or get_llm()

    def run(self,state):
        b=state["brief"]
        platforms=list(dict.fromkeys(b.get("platforms",[]) or []))
        duration=max(1,int(b.get("duration_days",30) or 30))
        strategy=state.get("strategy",{})
        items=[]

        # The submission/demo workflow intentionally keeps the calendar concise:
        # exactly one platform-specific item for every selected platform.
        for index,p in enumerate(platforms):
            if duration == 1:
                day_offset=0
            else:
                day_offset=round(index*(duration-1)/max(len(platforms)-1,1))
            topic=self._topic(p,b,index,len(platforms))
            body=self._generate(p,b,topic,strategy)
            items.append({
                "platform":p,
                "content_type":"email" if p.lower()=="email" else "post",
                "topic":topic,
                "body":body,
                "scheduled_date":(date.today()+timedelta(days=day_offset)).isoformat(),
            })
        return {"content":items,"status":"completed"}

    def _topic(self,p,b,i,n):
        phases=["problem awareness","solution education","feature/value proof","conversion CTA"]
        phase=phases[min(len(phases)-1, round(i*len(phases)/max(n,1)))]
        return f"{b.get('product_name','Product')} — {phase} for {p}"

    def _generate(self,p,b,topic,strategy):
        prompt=f"""Create original marketing content. Platform: {p}. Product: {b.get('product_name')}. Description: {b.get('description')}. Audience: {b.get('target_audience')}. Objective: {b.get('objective')}. Tone: {b.get('brand_tone')}. Guidelines: {b.get('brand_guidelines')}. Topic: {topic}. Strategy: {strategy}. Do not invent statistics, guarantees, rankings, customers, certifications, or unsupported product capabilities. Return only the finished copy."""
        text=self.llm.generate(prompt)
        if text and not text.startswith("Demo LLM output") and not text.startswith("LLM fallback:"):
            return text.strip()
        return self._fallback(p,b,topic)

    def _fallback(self,p,b,topic):
        product=b.get('product_name','Product'); audience=b.get('target_audience','your team'); objective=b.get('objective','your marketing objective')
        if p.lower()=="email":
            return f"Subject: A practical way to support {objective}\n\n{audience} can explore how {product} is designed to support everyday workflow needs. Review the approach, evaluate the fit for your team, and learn more."
        if p.lower()=="instagram":
            return f"A simpler way to think about {topic}. {product} is designed to support {audience}. Explore the product and see whether it fits your workflow. #AI #Marketing"
        return f"{audience} face workflow challenges that can slow progress. {product} is designed to support a more structured approach. Learn how it can help with {objective}, then evaluate whether it fits your needs."
