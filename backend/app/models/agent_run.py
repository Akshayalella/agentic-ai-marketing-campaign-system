from sqlalchemy import Column,Integer,String,Text,DateTime,ForeignKey
from datetime import datetime, timezone
from app.core.database import Base
class AgentRun(Base):
    __tablename__="agent_runs"
    id=Column(Integer,primary_key=True)
    campaign_id=Column(Integer,ForeignKey("campaigns.id"),nullable=False)
    agent_name=Column(String(120),nullable=False)
    status=Column(String(40),default="completed")
    output=Column(Text,default="")
    created_at=Column(DateTime,default=lambda: datetime.now(timezone.utc))
