class HumanApprovalAgent:
    name="Human Approval Workflow"
    def approve(self,item): item.approval_status="approved"; return item
    def reject(self,item,comment=""): item.approval_status="rejected"; item.review_notes=comment; return item
