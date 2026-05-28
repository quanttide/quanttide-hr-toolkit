from fastapi import FastAPI

from fastapi_quanttide_hr.routers import pipeline, recruitments


def create_app() -> FastAPI:
    app = FastAPI(
        title="QtCloud HR",
        description="招聘系统 — 招聘进度追踪",
        version="0.1.0",
    )
    app.include_router(recruitments.router)
    app.include_router(pipeline.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
