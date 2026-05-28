from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import pipeline, recruitments


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="QtCloud HR",
    description="招聘系统 MVP — 申请者管道管理",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(recruitments.router)
app.include_router(pipeline.router)


@app.get("/health")
def health():
    return {"status": "ok"}
