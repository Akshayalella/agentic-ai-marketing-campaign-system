from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class ApprovalStep(Base):
    __tablename__="approval_steps"
    id=Column(Integer,primary_key=True)
    content_id=Column(Integer,ForeignKey("content_items.id"),nullable=False)
    status=Column(String(40),default="pending")
    comment=Column(Text,default="")
    updated_at=Column(DateTime,default=lambda: datetime.now(timezone.utc))
