from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List
class CampaignCreate(BaseModel):
    product_name:str=Field(min_length=2)
    description:str=""
    target_audience:str=""
    objective:str="Generate qualified leads"
    budget:float=Field(ge=0)
    duration_days:int=Field(default=30,ge=1,le=365)
    platforms:List[str]=["LinkedIn","Email","Instagram"]
    brand_tone:str="Professional"
    brand_guidelines:str=""
class CampaignOut(CampaignCreate):
    id:int
    status:str
    workflow_status:str
    @field_validator("platforms",mode="before")
    @classmethod
    def normalize_platforms(cls,v):
        if isinstance(v,str): return [x for x in v.split(",") if x]
        return v
    model_config = ConfigDict(from_attributes=True)
