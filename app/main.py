from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine, SessionLocal
from app import models  # noqa: F401  -- ensures all models are registered before create_all
from app.routers import (
    auth, categories, products, variants, orders, uploads, dashboard,
    settings as settings_router, sections, store_info,
)
from app.services.auth_service import ensure_default_admin
from fastapi.responses import FileResponse
from pathlib import Path
# Creates tables if they don't exist yet. For real schema evolution over time,
# switch to Alembic migrations (scaffolding included in /alembic) instead of
# relying on create_all.
Base.metadata.create_all(bind=engine)

# Bootstraps a default admin from ADMIN_USERNAME/ADMIN_PASSWORD env vars, but
# only if the admins table is currently empty. See ensure_default_admin's
# docstring -- this is a no-op on every run after the first admin exists.
_db = SessionLocal()
try:
    ensure_default_admin(_db)
finally:
    _db.close()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Wildcard support: browsers reject allow_credentials=True combined with
# allow_origins=["*"]. Since auth here is a Bearer JWT (not cookies), we
# don't actually need credentialed CORS requests -- so when ALLOWED_ORIGINS
# is set to "*" we simply drop allow_credentials instead of restricting it.
_wildcard = "*" in settings.allowed_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _wildcard else settings.allowed_origins_list,
    allow_credentials=not _wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(variants.router)
app.include_router(orders.router)
app.include_router(uploads.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)
app.include_router(sections.router)
app.include_router(store_info.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"

app.mount(
    "/assets",
    StaticFiles(directory=DIST_DIR / "assets"),
    name="assets",
)


@app.get("/{path:path}")
async def serve_react(path: str):
    return FileResponse(DIST_DIR / "index.html")
