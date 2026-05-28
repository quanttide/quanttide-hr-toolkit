from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_quanttide_hr import create_app
from fastapi_quanttide_hr.database import Base, get_db as lib_get_db

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


sub_app = create_app()
sub_app.dependency_overrides[lib_get_db] = app_get_db

app = FastAPI()
app.mount("", sub_app)
