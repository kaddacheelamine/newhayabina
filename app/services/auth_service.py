from sqlalchemy.orm import Session

from app.config import settings
from app.models.admin import Admin
from app.security.hashing import verify_password, hash_password
from app.security.jwt import create_access_token


def authenticate_admin(db: Session, username: str, password: str) -> Admin | None:
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.password_hash):
        return None
    return admin


def create_token_for_admin(admin: Admin) -> str:
    return create_access_token(subject=str(admin.id))


def ensure_default_admin(db: Session) -> None:
    """
    Creates a default admin from ADMIN_USERNAME / ADMIN_PASSWORD env vars,
    but ONLY if the admins table is completely empty. This is meant purely
    to bootstrap a brand-new deployment (e.g. on Render, where you can set
    these as environment variables and never touch a shell). It deliberately
    never runs again once at least one admin exists, so it can't be used to
    reset or overwrite an existing admin's password -- change passwords via
    the app itself, not by editing env vars.
    """
    if not settings.admin_username or not settings.admin_password:
        return  # feature disabled unless both are explicitly set

    if db.query(Admin).first() is not None:
        return  # at least one admin already exists -- never touch it

    admin = Admin(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password),
        role=settings.admin_role,
    )
    db.add(admin)
    db.commit()
    print(f"[startup] Created default admin '{settings.admin_username}' (role={settings.admin_role})")
