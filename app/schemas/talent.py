from datetime import datetime

from pydantic import BaseModel

from app.models.talent import TalentStatus


class TalentCreate(BaseModel):
    email: str
    real_name: str


class TalentUpdate(BaseModel):
    pass


class TalentTransition(BaseModel):
    status: TalentStatus


class TalentRead(BaseModel):
    id: int
    recruitment_id: int
    email: str
    real_name: str
    status: TalentStatus
    created_at: datetime

    model_config = {"from_attributes": True}
