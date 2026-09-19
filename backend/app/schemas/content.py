from pydantic import BaseModel
class ContentUpdate(BaseModel): body:str
class ApprovalRequest(BaseModel): comment:str=""
