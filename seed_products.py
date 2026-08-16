"""
seed_products.py

Connects to the Storefront API and creates random test products for
demo/testing purposes, matching the current data model: a product has
1-3 variants, each with its own unique name, a single color, ONE photo,
and its own list of sizes with quantities.

No external image service needed -- images are generated locally with
Pillow (a solid color background + the variant name), so this works
even with no internet access beyond your own API.

Usage:
    pip install requests pillow
    python3 seed_products.py --api-url https://your-api.onrender.com --username admin --password yourpassword --count 10

Options:
    --api-url        Base URL of the API (default: http://127.0.0.1:8000)
    --username       Admin username (required)
    --password       Admin password (required)
    --count          Number of products to create (default: 10)
    --seed           Random seed, for reproducible runs (optional)
"""

import argparse
import io
import itertools
import random
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

ADJECTIVES = [
    "Comfort", "Classic", "Premium", "Cozy", "Elegant", "Casual",
    "Modern", "Soft", "Luxury", "Essential", "Everyday", "Deluxe",
]
NOUNS = [
    "Pajama Set", "T-Shirt", "Hoodie", "Bathrobe", "Nightgown",
    "Sweatpants", "Slippers", "Cardigan", "Sleep Shirt", "Jogger Set",
]
CATEGORIES = ["Pajamas", "Loungewear", "Outerwear", "Accessories", "Footwear"]
COLORS = ["Black", "White", "Pink", "Navy", "Grey", "Beige", "Red", "Green"]
SIZES = ["S", "M", "L", "XL"]
MATERIALS = ["Cotton", "Wool", "Polyester", "Linen", "Cotton Blend", "Fleece", "Silk"]
SEASONS = ["SUMMER", "WINTER", "SPRING", "AUTUMN", "ALL_SEASON"]

DESCRIPTION_TEMPLATES = [
    "Made from breathable, ultra-soft fabric designed for all-day comfort.",
    "A wardrobe staple that pairs easily with anything you own.",
    "Lightweight and durable, perfect for everyday wear or relaxing at home.",
    "Crafted with attention to detail and a focus on lasting comfort.",
    "Soft to the touch with a relaxed fit that moves with you.",
]

IMAGE_BG_COLORS = {
    "Black": (60, 60, 60), "White": (235, 235, 235), "Pink": (235, 200, 210),
    "Navy": (50, 65, 100), "Grey": (150, 150, 150), "Beige": (225, 210, 180),
    "Red": (190, 60, 60), "Green": (70, 150, 90),
}

# A global counter guarantees every variant name is unique across the
# whole seeding run, matching the API's store-wide unique-name constraint.
_name_counter = itertools.count(1)


def log(msg: str) -> None:
    print(msg, flush=True)


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def login(self, username: str, password: str) -> None:
        resp = self.session.post(
            f"{self.base_url}/api/auth/login",
            data={"username": username, "password": password},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        log(f"Logged in as '{username}'.")

    def get_or_create_category(self, name: str) -> int:
        resp = self.session.get(f"{self.base_url}/api/categories")
        resp.raise_for_status()
        for cat in resp.json():
            if cat["name"] == name:
                return cat["id"]

        resp = self.session.post(f"{self.base_url}/api/categories", json={"name": name})
        resp.raise_for_status()
        return resp.json()["id"]

    def create_product(
        self,
        name: str,
        description: str,
        price: float,
        category_id: int,
        material: str,
        season: str,
        discount_percentage: float,
    ) -> int:
        payload = {
            "name": name,
            "description": description,
            "price": price,
            "category_id": category_id,
            "material": material,
            "season": season,
            "discount_percentage": discount_percentage,
        }
        resp = self.session.post(f"{self.base_url}/api/products", json=payload)
        resp.raise_for_status()
        return resp.json()["id"]

    def create_variant(self, product_id: int, name: str, color: str, sizes: list[dict]) -> int:
        payload = {"name": name, "color": color, "sizes": sizes}
        resp = self.session.post(
            f"{self.base_url}/api/products/{product_id}/variants", json=payload
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def set_variant_image(self, variant_id: int, image_bytes: bytes, filename: str) -> None:
        files = {"file": (filename, image_bytes, "image/png")}
        resp = self.session.put(
            f"{self.base_url}/api/variants/{variant_id}/image", files=files
        )
        resp.raise_for_status()


def generate_variant_image(variant_name: str, color: str) -> bytes:
    """Generates a simple 600x600 PNG using a background color that
    actually matches the variant's color name, with the variant name
    stamped on it."""
    bg = IMAGE_BG_COLORS.get(color, (200, 200, 200))
    text_color = (240, 240, 240) if sum(bg) < 380 else (40, 40, 40)

    img = Image.new("RGB", (600, 600), color=bg)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
    except OSError:
        font = ImageFont.load_default()

    words = variant_name.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) > 520:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)

    total_height = len(lines) * 40
    y = (600 - total_height) // 2
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((600 - w) / 2, y), line, fill=text_color, font=font)
        y += 40

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def random_product_name() -> str:
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"


def random_description() -> str:
    return random.choice(DESCRIPTION_TEMPLATES)


def random_price() -> float:
    return round(random.uniform(9.99, 89.99), 2)


def random_discount() -> float:
    """70% of products have no discount; the rest get a random markdown,
    so seeded data actually exercises the discount/final_price behavior."""
    if random.random() < 0.7:
        return 0.0
    return round(random.choice([0.10, 0.15, 0.20, 0.25, 0.30, 0.50]), 2)


def unique_variant_name(base_name: str, color: str) -> str:
    """Store-wide unique names are required by the API -- append a running
    counter so re-runs (or many variants sharing a base product name +
    color) never collide."""
    n = next(_name_counter)
    return f"{base_name} - {color} #{n}"


def seed(client: ApiClient, count: int) -> None:
    category_ids = {name: client.get_or_create_category(name) for name in CATEGORIES}
    log(f"Categories ready: {list(category_ids.keys())}")

    for i in range(1, count + 1):
        base_name = random_product_name()
        description = random_description()
        price = random_price()
        category_name = random.choice(CATEGORIES)
        category_id = category_ids[category_name]
        material = random.choice(MATERIALS)
        season = random.choice(SEASONS)
        discount_percentage = random_discount()

        product_id = client.create_product(
            base_name, description, price, category_id, material, season, discount_percentage
        )
        discount_note = f", {int(discount_percentage * 100)}% off" if discount_percentage else ""
        log(
            f"[{i}/{count}] Created product #{product_id}: '{base_name}' "
            f"({category_name}, {material}, {season}, ${price}{discount_note})"
        )

        # 1-3 variants per product, each its own color + unique name +
        # its own sizes + its own single photo.
        num_variants = random.randint(1, 3)
        colors = random.sample(COLORS, k=num_variants)

        for color in colors:
            variant_name = unique_variant_name(base_name, color)
            sizes_for_variant = random.sample(SIZES, k=random.randint(1, len(SIZES)))
            sizes_payload = [
                {"size": size, "quantity": random.randint(0, 20)} for size in sizes_for_variant
            ]

            variant_id = client.create_variant(product_id, variant_name, color, sizes_payload)
            image_bytes = generate_variant_image(variant_name, color)
            client.set_variant_image(variant_id, image_bytes, f"variant_{variant_id}.png")

            sizes_desc = ", ".join(f"{s['size']}x{s['quantity']}" for s in sizes_payload)
            log(f"    variant '{variant_name}' ({color}): {sizes_desc} + image")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    client = ApiClient(args.api_url)
    try:
        client.login(args.username, args.password)
    except requests.HTTPError as exc:
        log(f"Login failed: {exc}")
        sys.exit(1)

    try:
        seed(client, args.count)
    except requests.HTTPError as exc:
        log(f"Request failed: {exc}")
        if exc.response is not None:
            log(f"Response body: {exc.response.text}")
        sys.exit(1)

    log(f"\nDone. Created {args.count} products.")


if __name__ == "__main__":
    main()
