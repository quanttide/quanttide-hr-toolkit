from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_quanttide_hr.database import Base, get_db as lib_get_db
from fastapi_quanttide_hr.routers import pipeline, recruitments

DATABASE_URL = "sqlite:///./hr.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def app_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Provider HR", description="招聘进度追踪示例")
app.dependency_overrides[lib_get_db] = app_get_db
app.include_router(recruitments.router)
app.include_router(pipeline.router)
