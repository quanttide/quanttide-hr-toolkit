from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_quanttide_hr.database import Base, engine
from fastapi_quanttide_hr.routers import pipeline, recruitments


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="QtCloud HR",
        description="招聘系统 — 招聘进度追踪",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(recruitments.router)
    app.include_router(pipeline.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
