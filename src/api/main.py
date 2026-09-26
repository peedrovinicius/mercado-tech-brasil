from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routers import analytics, metadata, overview, provenance, quality, system
from src.core.settings import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=(
        "API de indicadores reproduzíveis do mercado formal de trabalho em tecnologia no Brasil. "
        "Fontes, cobertura e qualidade dos dados são expostas pela própria API."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(system.router, prefix="/api/v1")
app.include_router(metadata.router, prefix="/api/v1")
app.include_router(quality.router, prefix="/api/v1")
app.include_router(overview.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(provenance.router, prefix="/api/v1")


frontend_dist = Path(settings.root) / "frontend" / "dist"

if frontend_dist.exists():
    app.mount(
        "/",
        StaticFiles(directory=frontend_dist, html=True),
        name="frontend",
    )
else:

    @app.get("/", tags=["root"])
    def root() -> dict[str, str]:
        return {
            "project": settings.project_name,
            "version": settings.version,
            "docs": "/docs",
            "health": "/api/v1/system/health",
            "sources": "/api/v1/metadata/sources",
        }
