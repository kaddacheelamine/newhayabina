from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.models.settings import SiteSetting

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    """Public -- storefront settings (e.g. shipping fee, store name) are
    needed by the frontend without requiring login."""
    rows = db.query(SiteSetting).all()
    return {row.key: row.value for row in rows}


@router.put("/{key}")
def upsert_setting(key: str, value: str, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    setting = db.query(SiteSetting).filter(SiteSetting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = SiteSetting(key=key, value=value)
        db.add(setting)
    db.commit()
    return {"key": key, "value": value}
