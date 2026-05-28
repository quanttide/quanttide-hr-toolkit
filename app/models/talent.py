import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TalentStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    EXAM_SENT = "exam_sent"
    EXAM_RECEIVED = "exam_received"
    EVALUATING = "evaluating"
    INTERVIEW = "interview"
    OFFER = "offer"
    CLOSED = "closed"


STATUS_TRANSITIONS = {
    TalentStatus.NEW: [TalentStatus.CONTACTED, TalentStatus.CLOSED],
    TalentStatus.CONTACTED: [TalentStatus.EXAM_SENT, TalentStatus.CLOSED],
    TalentStatus.EXAM_SENT: [TalentStatus.EXAM_RECEIVED, TalentStatus.CLOSED],
    TalentStatus.EXAM_RECEIVED: [TalentStatus.EVALUATING, TalentStatus.CLOSED],
    TalentStatus.EVALUATING: [TalentStatus.INTERVIEW, TalentStatus.EXAM_SENT, TalentStatus.CLOSED],
    TalentStatus.INTERVIEW: [TalentStatus.OFFER, TalentStatus.CLOSED],
    TalentStatus.OFFER: [TalentStatus.CLOSED],
    TalentStatus.CLOSED: [],
}


class Talent(Base):
    __tablename__ = "talents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recruitment_id: Mapped[int] = mapped_column(ForeignKey("recruitments.id"), index=True)
    email: Mapped[str] = mapped_column(String(200))
    real_name: Mapped[str] = mapped_column(String(100))

    status: Mapped[TalentStatus] = mapped_column(Enum(TalentStatus), default=TalentStatus.NEW, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


