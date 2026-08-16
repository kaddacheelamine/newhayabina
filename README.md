# Storefront API (FastAPI)

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # edit SECRET_KEY at minimum
python3 create_admin.py admin yourpassword super_admin

uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Site branding: `/api/store-info`

A dedicated endpoint the frontend calls to get the homepage title,
description, and banner image -- so the storeowner can change these
without a code deploy.

- `GET /api/store-info` -- public. Returns `{title, description, banner_image_path}`.
  Never 404s -- returns nulls if nothing's been set yet.
- `PUT /api/store-info` -- admin only, **multipart form** (not JSON), so
  the banner image can be updated in the same request as the text:
  ```bash
  curl -X PUT $API/api/store-info \
    -H "Authorization: Bearer $TOKEN" \
    -F "title=My Store" \
    -F "description=Best pajamas in town" \
    -F "image=@banner.jpg"
  ```
  Send only the fields you're changing -- omitted fields are left as-is.

`banner_image_path` follows the same convention as product images: it's a
relative path, not a full URL. Build the real URL the same way:
`${API_BASE_URL}/uploads/${banner_image_path}`.

## Variants are the sellable unit

This is the core data model, and it changed from earlier -- **a variant now
carries its own name, one color, one photo, and its own list of sizes**.
A "Red" version of a product and a "Green" version are two separate
variants, even though they share the parent product's name/price/description.

```
Product (name, price, description, material, season, discount...)
  └─ Variant (name [unique store-wide], color, one image)
       └─ sizes: [{size, quantity}, {size, quantity}, ...]
```

There is **no separate product-level image list** -- a product's photo
gallery is simply the union of each of its variants' single image. There's
also no `ProductImage` table anymore.

### Creating a variant

```bash
curl -X POST $API/api/products/{product_id}/variants \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
    "name": "Classic Pajama Set - Red",
    "color": "Red",
    "sizes": [{"size": "S", "quantity": 5}, {"size": "M", "quantity": 8}]
  }'
```
- `name` must be unique **across the whole store**, not just within one
  product -- creating a second variant anywhere with the same name (case
  insensitive) gets a `409`. (If you actually want uniqueness scoped per
  product instead, say so -- it's a one-line change.)
- `sizes` is required, at least one entry. Different variants of the same
  product can have completely different size lists -- that's expected
  (e.g. Red comes in S/M/L, Green only comes in M).

### Setting the variant's photo

Separate endpoint, since it's a file upload:
```bash
curl -X PUT $API/api/variants/{variant_id}/image \
  -H "Authorization: Bearer $TOKEN" -F "file=@red_photo.jpg"
```
Calling it again replaces the photo (the old file is deleted automatically).

### Updating / deleting a variant

```bash
PUT /api/variants/{id}     # update name, color, and/or sizes (JSON)
DELETE /api/variants/{id}  # deletes the variant, its sizes, and its image file
```
`sizes` in a `PUT` **replaces the entire list** -- send the full set of
sizes you want, not just the ones changing. This keeps the semantics
simple and unambiguous (no guessing whether an omitted size should be
kept or removed).

### What the frontend gets back

```json
{
  "id": 1,
  "name": "Classic Pajama Set",
  "price": "49.99",
  "colors": ["Red", "Green"],
  "stock": 22,
  "variants": [
    {
      "id": 1, "name": "Classic Pajama Set - Red", "color": "Red",
      "image_path": "products/abc123.jpg",
      "sizes": [{"size": "S", "quantity": 5}, {"size": "M", "quantity": 8}],
      "total_quantity": 13, "is_out_of_stock": false
    },
    {
      "id": 2, "name": "Classic Pajama Set - Green", "color": "Green",
      "image_path": "products/def456.jpg",
      "sizes": [{"size": "M", "quantity": 6}],
      "total_quantity": 6, "is_out_of_stock": false
    }
  ]
}
```

Frontend flow this is built for:
1. Show each variant's photo (`variants[i].image_path`) as a tappable
   thumbnail -- tapping one *is* the color selection, since the color is
   already visible in the photo. No separate color swatch/dropdown needed.
2. Once a variant (photo) is picked, show `variants[i].sizes` as the size
   options -- that's the only thing the customer still explicitly chooses.

### Ordering: product + variant + size + quantity

```json
POST /api/orders
{
  "customer": {...},
  "delivery_type": "HOME", "wilaya": "...", "commune": "...",
  "items": [
    {"product_id": 1, "variant_id": 1, "size": "M", "quantity": 2}
  ]
}
```
The order response's items now include everything needed to display the
order without extra lookups:
```json
{"product_id": 1, "product_name": "Classic Pajama Set",
 "variant_id": 1, "variant_name": "Classic Pajama Set - Red",
 "size": "M", "quantity": 2, "price": "49.99"}
```
Stock deduction/restoration on confirm/cancel now happens against the
specific `(variant_id, size)` combination, not the variant as a whole --
ordering 2 in size M only affects M's quantity, not S or L.

### Migrating an existing database

This is a structural change (variants gain `name`/`image_path` and lose
`size`/`quantity`; a new `variant_sizes` table holds those instead; the
old `product_images` table is gone; `order_items` gains a `size` column).
There's no sensible way to auto-invent the missing `name`s for old
variant rows, so the migration is necessarily destructive to
variant/image/order-item data specifically:

```bash
python3 migrate_v3_variant_restructure.py
```
It asks for a typed `yes` confirmation, shows exactly which tables it's
about to drop, and **keeps** your products, categories, customers, orders
(the order records themselves), admins, sections, and site_info untouched.
Read the script's docstring before running it.

**If you're deploying on Render without a persistent disk** (the default,
per the ephemeral-filesystem discussion earlier): your database is already
wiped on every redeploy, so there's almost certainly no real data worth
preserving here -- just delete `database.db` and let `create_all` build
everything fresh instead of running this script at all.

## Site branding: `/api/store-info`

A dedicated endpoint the frontend calls to get the homepage title,
description, and banner image -- so the storeowner can change these
without a code deploy.

- `GET /api/store-info` -- public. Returns `{title, description, banner_image_path}`.
  Never 404s -- returns nulls if nothing's been set yet.
- `PUT /api/store-info` -- admin only, **multipart form** (not JSON), so
  the banner image can be updated in the same request as the text:
  ```bash
  curl -X PUT $API/api/store-info \
    -H "Authorization: Bearer $TOKEN" \
    -F "title=My Store" \
    -F "description=Best pajamas in town" \
    -F "image=@banner.jpg"
  ```
  Send only the fields you're changing -- omitted fields are left as-is.

`banner_image_path` follows the same convention as variant images: it's a
relative path, not a full URL. Build the real URL the same way:
`${API_BASE_URL}/uploads/${banner_image_path}`.

## Homepage sections: `/api/sections`

Lets the store owner create curated homepage blocks (e.g. "Summer
Collection", "New Arrivals"), each with a title and one or more
categories:

- `GET /api/sections` -- public. Returns e.g.:
  ```json
  [{"id": 1, "title": "Summer Collection", "display_order": 1,
    "categories": [{"id": 2, "name": "Pajamas"}, {"id": 5, "name": "Loungewear"}]}]
  ```
- `POST /api/sections` -- admin, `{"title": "...", "category_ids": [2, 5], "display_order": 1}`.
- `PUT /api/sections/{id}` / `DELETE /api/sections/{id}` -- admin.

A section only stores *which categories* it features, not products
directly -- the frontend fetches actual products per category via the
existing `GET /api/products?category_id=...`. This keeps sections
decoupled from product data (adding/removing products from a category
automatically updates what a section shows, with no extra step).

## Product fields: material, season, discount

Products carry three extra fields beyond the original spec:

- **`material`** -- free text (e.g. "Cotton", "Wool", "100% Polyester").
- **`season`** -- one of `SUMMER`, `WINTER`, `SPRING`, `AUTUMN`, `ALL_SEASON`, or `null`.
- **`discount_percentage`** -- a ratio from `0` (no discount) to `1` (100% off),
  e.g. `0.20` = 20% off. Validated at the API layer (rejects anything outside 0-1).

Every product response also includes a computed **`final_price`**
(`price * (1 - discount_percentage)`, rounded to 2 decimals) -- use this as
the price to actually display, and show `price` crossed out only when
`discount_percentage > 0`.

To turn a discount on/off later, just `PUT` the product with a new
`discount_percentage` -- e.g. `{"discount_percentage": "0.30"}` to start a
30%-off sale, or `{"discount_percentage": "0"}` to end it. No separate
endpoint needed.

**If you already have a deployed database from before this change**, run
the migration once against it (adds the missing columns without touching
existing data):
```bash
python3 migrate_add_product_fields.py
```
On Render: run this from the Shell tab, once, after deploying the updated
code. Safe to run more than once (it skips columns that already exist).
Brand-new databases don't need this -- `create_all` already includes the
new columns.

## Creating the first admin

Two ways, pick whichever fits your setup:

1. **CLI script** (`create_admin.py`) -- run it manually, locally or via
   Render's Shell tab. Good for a one-time setup or adding more admins later.

2. **Auto-bootstrap via env vars** -- set `ADMIN_USERNAME` and
   `ADMIN_PASSWORD` (see `.env.example`) as environment variables (e.g. in
   Render's dashboard). On startup, `main.py` calls
   `auth_service.ensure_default_admin`, which creates that admin **only if
   the admins table is completely empty**. This is meant for platforms with
   an ephemeral filesystem (like Render without a persistent disk), where
   the database gets wiped on every redeploy and you don't want to open a
   shell each time.

   Safe to leave these env vars set permanently: once an admin exists,
   `ensure_default_admin` becomes a no-op on every subsequent startup. It
   will never overwrite an existing admin's password -- change passwords
   through the app itself, not by editing env vars.

## What's here

Matches the architecture doc's structure (`models/`, `schemas/`, `routers/`,
`services/`, `security/`) and all the endpoints it specifies. A few
deliberate deviations from the original spec, based on issues that would
have caused bugs in production:

- **`Product.stock` is computed, not stored.** It sums every
  `VariantSize.quantity` across all of a product's variants, so there's
  one source of truth for inventory instead of numbers that can drift apart.
- **Stock is only touched on status transitions**, centralized in
  `services/order_service.py::update_order_status`. Placing an order
  (`POST /api/orders`) validates availability but doesn't reserve/deduct
  anything. Deduction happens the moment an order moves to `CONFIRMED`,
  against the specific `(variant, size)` ordered. If a confirmed (or
  later) order is then `CANCELLED`, the stock it had consumed is
  automatically restored to that same `(variant, size)`.
- **Status transitions are restricted** to a defined graph (see
  `_ALLOWED_TRANSITIONS` in `order_service.py`) so you can't, e.g., move a
  `CANCELLED` order back to `CONFIRMED` by mistake.
- **Every status change is logged** to `order_status_history` (order id,
  from/to status, which admin made the change, optional note) — useful
  both for support/audit and for debugging stock discrepancies later.
- **Admin has a `role` field** (`super_admin` / `staff`) even though
  there's only one admin type in the spec — cheap to add now, painful to
  migrate in later once there's real data.
- Variant images are set via a dedicated `PUT /api/variants/{id}/image`
  endpoint (one photo per variant) rather than a generic product-images
  upload — see "Variants are the sellable unit" above for why.

## Known limitations worth knowing about

- **SQLite has no row-level locking.** The availability check in
  `create_order` has a theoretical race window under concurrent orders
  for the last unit of a variant — the real deduction + hard check happens
  at confirmation time in `update_order_status`, which will correctly
  reject over-confirmation, but two PENDING orders can both be created
  for stock that only covers one. Fine for a low-concurrency single-admin
  storefront; if you move to Postgres/MySQL under real load, add
  `SELECT ... FOR UPDATE` in the confirm path.
- **No rate limiting** on the public `POST /api/orders` endpoint. Worth
  adding (e.g. `slowapi`, by IP or phone number) before going live, since
  it's an obvious target for spam.
- **JWT logout is client-side only** (stateless tokens, no server-side
  revocation list). Fine for an admin-only auth system with short-lived
  tokens; add a blocklist table if that ever matters.
- **Schema migrations use `create_all`**, not Alembic, for simplicity.
  Fine while the schema is still moving; switch to real Alembic
  migrations before you have production data you can't just wipe.

## Quick manual test

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -d "username=admin&password=yourpassword" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s http://127.0.0.1:8000/api/products -H "Authorization: Bearer $TOKEN"
```
