from datetime import datetime

from pydantic import BaseModel


class RecruitmentRead(BaseModel):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
