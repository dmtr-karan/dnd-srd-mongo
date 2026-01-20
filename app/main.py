from fastapi import FastAPI
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="SRD Grounding Service",
        version="0.1.0",
        description="Read-only SRD grounding API (P4).",
    )
    app.include_router(router)
    return app


app = create_app()
