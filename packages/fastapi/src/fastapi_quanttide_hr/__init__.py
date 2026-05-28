from fastapi import FastAPI

from fastapi_quanttide_hr.routers import pipeline, recruitments


def create_app(
    title: str = "HR Toolkit",
    description: str = "",
    version: str = "0.1.0",
) -> FastAPI:
    app = FastAPI(title=title, description=description, version=version)
    app.include_router(recruitments.router)
    app.include_router(pipeline.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
