"""Product catalog for Vision Kled. Super-admin can add more later."""

from __future__ import annotations

PRODUCTS: list[dict[str, str]] = [
    {
        "slug": "portfolio",
        "name_ar": "Vision Portfolio",
        "name_fr": "Vision Portfolio",
        "audience": "باحثون عن عمل ومستقلون",
        "price": "10–15 $/شهر",
        "setup": "10–30 $ مرة واحدة",
        "demo_template": "portfolio",
    },
    {
        "slug": "business",
        "name_ar": "Vision Presence",
        "name_fr": "Vision Presence",
        "audience": "محلات ومهن حرّة في تونس",
        "price": "15–20 $/شهر",
        "setup": "حسب الحاجة",
        "demo_template": "business",
    },
    {
        "slug": "bac",
        "name_ar": "Vision Bac",
        "name_fr": "Vision Bac",
        "audience": "تلاميذ الباكالوريا التونسية",
        "price": "5–10 $ لمدة 1–3 أشهر",
        "setup": "بدون",
        "demo_template": "",
    },
]


def get_product(slug: str) -> dict[str, str]:
    """Return a product by slug, defaulting to Vision Portfolio."""
    for item in PRODUCTS:
        if item["slug"] == slug:
            return item
    return PRODUCTS[0]
