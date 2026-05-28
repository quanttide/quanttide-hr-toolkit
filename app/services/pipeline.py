from sqlalchemy.orm import Session

from app.models.talent import Talent, TalentStatus


def get_pipeline(db: Session) -> dict:
    stages = {}
    total = 0
    for status in TalentStatus:
        talents = (
            db.query(Talent)
            .filter(Talent.status == status)
            .order_by(Talent.updated_at.desc())
            .all()
        )
        stages[status.value] = [_talent_to_card(t) for t in talents]
        total += len(talents)

    need_attention = len(stages.get("exam_received", [])) + len(stages.get("evaluating", []))
    return {
        "stages": stages,
        "summary": {
            "total": total,
            "by_stage": {s.value: len(stages.get(s.value, [])) for s in TalentStatus},
            "need_attention": need_attention,
        },
    }


def _talent_to_card(t: Talent) -> dict:
    return {
        "id": t.id,
        "email": t.email,
        "real_name": t.real_name,
        "recruitment_id": t.recruitment_id,
        "status": t.status.value,
        "created_at": t.created_at.isoformat(),
    }


def get_status_counts(db: Session) -> list[dict]:
    from sqlalchemy import func

    rows = (
        db.query(Talent.status, func.count(Talent.id))
        .group_by(Talent.status)
        .all()
    )
    return [{"status": status.value, "count": count} for status, count in rows]
