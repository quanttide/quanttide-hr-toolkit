from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.talent import STATUS_TRANSITIONS, Talent, TalentStatus
from app.models.recruitment import Recruitment
from app.schemas.talent import TalentCreate, TalentRead, TalentTransition, TalentUpdate
from app.schemas.recruitment import RecruitmentRead

router = APIRouter(prefix="/recruitments", tags=["recruitments"])


@router.get("", response_model=list[RecruitmentRead])
def list_recruitments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return db.query(Recruitment).order_by(Recruitment.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{recruitment_id}", response_model=RecruitmentRead)
def get_recruitment(recruitment_id: int, db: Session = Depends(get_db)):
    r = db.query(Recruitment).filter(Recruitment.id == recruitment_id).first()
    if not r:
        raise HTTPException(404, "Recruitment not found")
    return r


@router.post("", response_model=RecruitmentRead, status_code=201)
def create_recruitment(db: Session = Depends(get_db)):
    r = Recruitment()
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{recruitment_id}", status_code=204)
def delete_recruitment(recruitment_id: int, db: Session = Depends(get_db)):
    r = db.query(Recruitment).filter(Recruitment.id == recruitment_id).first()
    if not r:
        raise HTTPException(404, "Recruitment not found")
    db.delete(r)
    db.commit()


@router.get("/{recruitment_id}/talents", response_model=list[TalentRead])
def list_talents(
    recruitment_id: int,
    status: TalentStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    qb = db.query(Talent).filter(Talent.recruitment_id == recruitment_id)
    if status:
        qb = qb.filter(Talent.status == status)
    return qb.order_by(Talent.updated_at.desc()).offset(skip).limit(limit).all()


@router.get("/{recruitment_id}/talents/{talent_id}", response_model=TalentRead)
def get_talent(recruitment_id: int, talent_id: int, db: Session = Depends(get_db)):
    t = db.query(Talent).filter(Talent.id == talent_id, Talent.recruitment_id == recruitment_id).first()
    if not t:
        raise HTTPException(404, "Talent not found")
    return t


@router.post("/{recruitment_id}/talents", response_model=TalentRead, status_code=201)
def create_talent(recruitment_id: int, data: TalentCreate, db: Session = Depends(get_db)):
    recruitment = db.query(Recruitment).filter(Recruitment.id == recruitment_id).first()
    if not recruitment:
        raise HTTPException(404, "Recruitment not found")
    t = Talent(recruitment_id=recruitment_id, email=data.email, real_name=data.real_name)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.patch("/{recruitment_id}/talents/{talent_id}", response_model=TalentRead)
def update_talent(recruitment_id: int, talent_id: int, data: TalentUpdate, db: Session = Depends(get_db)):
    t = db.query(Talent).filter(Talent.id == talent_id, Talent.recruitment_id == recruitment_id).first()
    if not t:
        raise HTTPException(404, "Talent not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.post("/{recruitment_id}/talents/{talent_id}/transition", response_model=TalentRead)
def transition_talent(recruitment_id: int, talent_id: int, data: TalentTransition, db: Session = Depends(get_db)):
    t = db.query(Talent).filter(Talent.id == talent_id, Talent.recruitment_id == recruitment_id).first()
    if not t:
        raise HTTPException(404, "Talent not found")

    target = data.status
    if target not in STATUS_TRANSITIONS.get(t.status, []):
        raise HTTPException(400, f"Cannot transition from {t.status.value} to {target.value}")

    t.status = target
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{recruitment_id}/talents/{talent_id}", status_code=204)
def delete_talent(recruitment_id: int, talent_id: int, db: Session = Depends(get_db)):
    t = db.query(Talent).filter(Talent.id == talent_id, Talent.recruitment_id == recruitment_id).first()
    if not t:
        raise HTTPException(404, "Talent not found")
    db.delete(t)
    db.commit()
