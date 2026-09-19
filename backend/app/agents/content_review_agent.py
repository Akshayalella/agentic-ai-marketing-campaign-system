import re

class ContentReviewBrandComplianceAgent:
    name="Content Review & Brand Compliance Agent"
    def run(self,state):
        b=state["brief"]; guidelines=(b.get("brand_guidelines") or "").lower(); tone=(b.get("brand_tone") or "professional").lower()
        forbidden=["guaranteed","100%","best in the world","#1","number one","no. 1"]
        reviewed=[]
        for item in state.get("content",[]):
            text=item.get("body",""); lower=text.lower(); issues=[]
            claims=[w for w in forbidden if w in lower]
            if claims: issues.append("Unsupported or absolute claim: "+", ".join(claims))
            if re.search(r"\b\d+(?:\.\d+)?%\b",text) and not re.search(r"\b(?:source|according to|study|report)\b",lower):
                issues.append("Percentage claim has no visible source attribution")
            if not item.get("body","").strip(): issues.append("Missing content")
            if guidelines and "avoid unsupported claims" in guidelines and claims:
                issues.append("Violates supplied brand guideline")
            status="rejected" if issues else "approved_for_human_review"
            reviewed.append({**item,"review_status":status,"review_notes":"; ".join(issues) if issues else f"Passes automated claim checks; tone target: {tone}. Human approval is still required."})
        return {"reviewed_content":reviewed,"status":"completed"}
