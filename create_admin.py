"""
One-off CLI script to create the first admin account.

Usage:
    python create_admin.py <username> <password> [role]

role defaults to 'super_admin'. Valid roles: super_admin, staff.
"""
import sys

from app.database import Base, engine, SessionLocal
from app import models  # noqa: F401
from app.models.admin import Admin
from app.models.enums import AdminRole
from app.security.hashing import hash_password


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else AdminRole.SUPER_ADMIN.value

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Admin).filter(Admin.username == username).first():
            print(f"Admin '{username}' already exists.")
            sys.exit(1)

        admin = Admin(username=username, password_hash=hash_password(password), role=role)
        db.add(admin)
        db.commit()
        print(f"Created admin '{username}' with role '{role}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
