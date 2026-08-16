"""
migrate_add_product_fields.py

Adds the new `material`, `season`, and `discount_percentage` columns to an
EXISTING `products` table. This is needed because SQLAlchemy's
`Base.metadata.create_all()` (used in app/main.py) only creates tables that
don't exist yet -- it does NOT add new columns to a table that's already
there. Without running this, a database created before this update will be
missing these columns and every product read/write will error.

Safe to run multiple times: it checks which columns already exist first and
only adds the ones that are missing.

Usage (run once, against whichever database you're updating):
    python3 migrate_add_product_fields.py

On Render: open the Shell tab for your service and run the same command --
it uses the same DATABASE_URL your app already runs with.

NOTE: SQLite does not support adding a CHECK constraint to an existing
table via ALTER TABLE (only via a full table rebuild). This script adds the
columns without that DB-level constraint; range validation (0-1) still
happens at the API layer via Pydantic. Brand new databases (created fresh
via create_all) get the CHECK constraint automatically since it's part of
the model definition.
"""

from sqlalchemy import inspect, text

from app.database import engine

NEW_COLUMNS = {
    "material": "VARCHAR(128)",
    "season": "VARCHAR(16)",
    "discount_percentage": "NUMERIC(3, 2) NOT NULL DEFAULT 0",
}


def main():
    inspector = inspect(engine)
    existing_columns = {col["name"] for col in inspector.get_columns("products")}

    with engine.begin() as conn:
        for column_name, column_def in NEW_COLUMNS.items():
            if column_name in existing_columns:
                print(f"Skipping '{column_name}' -- already exists.")
                continue
            print(f"Adding column '{column_name}'...")
            conn.execute(text(f"ALTER TABLE products ADD COLUMN {column_name} {column_def}"))
            print(f"  done.")

    print("Migration complete.")


if __name__ == "__main__":
    main()
