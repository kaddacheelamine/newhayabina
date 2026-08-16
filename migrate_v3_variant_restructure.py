"""
migrate_v3_variant_restructure.py

Applies the "variants are the sellable unit" restructuring to an EXISTING
database:
    - product_variants: used to be (color, size, quantity) rows. Now it's
      (name [unique], color, image_path), with sizes/quantities moved out
      to a new variant_sizes table.
    - product_images: removed entirely. A product's image gallery is now
      just the union of its variants' single image.
    - order_items: gains a required `size` column.

WHY THIS SCRIPT IS DESTRUCTIVE (read before running):
This is a structural change, not just new columns -- old variant rows
don't have a `name` or `image_path`, and old order_items don't have a
`size`. There's no sensible automatic way to invent that missing data.
So this script DROPS the affected tables and lets the app's normal
`create_all()` recreate them empty on next startup.

What you KEEP: products, categories, customers, orders (the order
records themselves), admins, sections, site_info -- all untouched.
What you LOSE: all existing variants (name/color/sizes/images), and the
line-items of existing orders (the orders themselves still exist, just
empty of items).

If you're running on Render without a persistent disk (as discussed
earlier), your database is already wiped on every redeploy, so there is
almost certainly nothing here worth preserving -- just delete
database.db entirely and let the app recreate everything fresh instead
of running this script. This script exists for the case where you *do*
have real product/customer/order data you want to keep and are only
willing to lose variant/image details.

Usage:
    python3 migrate_v3_variant_restructure.py
Then restart the app once (or it'll happen automatically on the next
Render deploy) so create_all() rebuilds the new tables.
"""

from sqlalchemy import inspect, text

from app.database import engine

TABLES_TO_DROP = ["product_images", "order_items", "product_variants"]


def main():
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    print("This will DROP the following tables if present:")
    for t in TABLES_TO_DROP:
        present = "exists" if t in existing_tables else "not present, skipping"
        print(f"  - {t} ({present})")
    print()
    confirm = input("Type 'yes' to continue: ").strip().lower()
    if confirm != "yes":
        print("Aborted, nothing was changed.")
        return

    with engine.begin() as conn:
        for table in TABLES_TO_DROP:
            if table in existing_tables:
                print(f"Dropping {table}...")
                conn.execute(text(f"DROP TABLE {table}"))

    print("\nDone. Restart the app (or redeploy) so create_all() rebuilds")
    print("product_variants, variant_sizes, and order_items with the new schema.")


if __name__ == "__main__":
    main()
