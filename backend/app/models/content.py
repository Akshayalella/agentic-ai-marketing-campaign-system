from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime, timezone
from app.core.database import Base
class ContentItem(Base):
    __tablename__="content_items"
    id=Column(Integer,primary_key=True,index=True)
    campaign_id=Column(Integer,ForeignKey("campaigns.id"),nullable=False)
    platform=Column(String(50),nullable=False)
    content_type=Column(String(80),default="post")
    topic=Column(String(300),default="")
    body=Column(Text,default="")
    approval_status=Column(String(40),default="pending")
    publishing_status=Column(String(40),default="not_published")
    review_status=Column(String(40),default="pending")
    review_notes=Column(Text,default="")
    scheduled_date=Column(String(20),default="")
    created_at=Column(DateTime,default=lambda: datetime.now(timezone.utc))
