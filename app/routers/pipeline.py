from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.pipeline import get_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("")
def pipeline(db: Session = Depends(get_db)):
    return get_pipeline(db)
