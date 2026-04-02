from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routers import appointments, booking, catalog, me, pricelist

FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Beauty Salon API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://web.telegram.org", "null"],
        allow_origin_regex=r"https://.*\.telegram\.org",
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
    app.include_router(booking.router, prefix="/api/v1/booking", tags=["booking"])
    app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["appointments"])
    app.include_router(pricelist.router, prefix="/api/v1", tags=["pricelist"])
    app.include_router(me.router, prefix="/api/v1", tags=["me"])

    # Health check — used by Railway healthcheck
    @app.get("/api/v1/health", tags=["health"], include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok"}

    # Serve React SPA (only if build exists)
    if FRONTEND_DIST.exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str = "") -> FileResponse:
            # API routes are already handled above; this catches everything else
            if full_path.startswith("api/"):
                from fastapi import HTTPException
                raise HTTPException(status_code=404)
            return FileResponse(FRONTEND_DIST / "index.html")

    return app
