from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.models.admin import Admin
from app.schemas.auth import TokenResponse, AdminOut
from app.services.auth_service import authenticate_admin, create_token_for_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = authenticate_admin(db, form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_token_for_admin(admin)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AdminOut)
def me(current_admin: Admin = Depends(get_current_admin)):
    return current_admin


@router.post("/logout")
def logout():
    # JWTs are stateless -- logout is handled client-side by discarding the token.
    # If a server-side blocklist is ever needed, add a revoked-token table here.
    return {"detail": "Logged out"}
