# apps/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from settings import settings
from apps.api.routers import health, articles, entity_review


def create_app() -> FastAPI:
    app = FastAPI(
        title="Posverdad API",
        version="0.1.0",
    )

    # CORS mínimo; se puede endurecer después
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: restringir en prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(articles.router)
    app.include_router(entity_review.router)

    return app


app = create_app()

# Ejemplo de uso:
# uv run --group api uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
