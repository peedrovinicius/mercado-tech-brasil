from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routers import analytics, metadata, overview, provenance, quality, rais, system
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


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(system.router, prefix="/api/v1")
app.include_router(metadata.router, prefix="/api/v1")
app.include_router(quality.router, prefix="/api/v1")
app.include_router(overview.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(rais.router, prefix="/api/v1")
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
