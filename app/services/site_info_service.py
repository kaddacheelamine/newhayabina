from sqlalchemy.orm import Session

from app.models.site_info import SiteInfo


def get_site_info(db: Session) -> SiteInfo:
    """Returns the singleton SiteInfo row, creating an empty one on first
    access so GET /api/store-info never 404s -- the frontend can render a
    blank state instead of handling a missing-resource error."""
    info = db.query(SiteInfo).filter(SiteInfo.id == 1).first()
    if not info:
        info = SiteInfo(id=1)
        db.add(info)
        db.commit()
        db.refresh(info)
    return info
