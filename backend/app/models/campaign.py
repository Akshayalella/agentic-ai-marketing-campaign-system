from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime, timezone
from app.core.database import Base
class Campaign(Base):
    __tablename__="campaigns"
    id=Column(Integer,primary_key=True,index=True)
    product_name=Column(String(200),nullable=False)
    description=Column(Text,default="")
    target_audience=Column(Text,default="")
    objective=Column(String(300),default="")
    budget=Column(Float,default=0)
    duration_days=Column(Integer,default=30)
    platforms=Column(String(500),default="LinkedIn,Email,Instagram")
    brand_tone=Column(String(100),default="Professional")
    brand_guidelines=Column(Text,default="")
    status=Column(String(50),default="draft")
    workflow_status=Column(String(80),default="not_started")
    projected_analytics=Column(Text,default="{}")
    observed_analytics=Column(Text,default="{}")
    created_at=Column(DateTime,default=lambda: datetime.now(timezone.utc))
