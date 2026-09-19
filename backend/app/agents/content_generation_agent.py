from datetime import date, timedelta
from app.services.llm_provider import get_llm

class ContentGenerationAgent:
    name="Content Generation Agent"
    def __init__(self,llm=None): self.llm=llm or get_llm()

    def run(self,state):
        b=state["brief"]; platforms=b.get("platforms",[]); n=max(1,int(b.get("duration_days",30)))
        items=[]; freq={"LinkedIn":3,"Email":1,"Instagram":2}
        strategy=state.get("strategy",{})
        for i in range(n):
            for p in platforms:
                interval=max(1,round(7/freq.get(p,1)))
                if i==0 or i % interval == 0:
                    topic=self._topic(p,b,i,n)
                    body=self._generate(p,b,topic,strategy)
                    items.append({"platform":p,"content_type":"email" if p.lower()=="email" else "post",
                                  "topic":topic,"body":body,"scheduled_date":(date.today()+timedelta(days=i)).isoformat()})
        return {"content":items,"status":"completed"}

    def _topic(self,p,b,i,n):
        phases=["problem awareness","solution education","feature/value proof","conversion CTA"]
        return f"{b.get('product_name','Product')} — {phases[min(3, int(i/max(n,1)*4))]} for {p}"

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
