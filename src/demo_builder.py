"""Fill a static HTML template and write a local demo site (Agent 3)."""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

from src.config import settings

logger = logging.getLogger("visionkled")

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "demos_output"


def slugify(value: str) -> str:
    """URL-safe slug from a person or business name."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    if slug:
        return slug
    # Arabic names often strip to empty via ASCII ignore — keep a stable hash.
    compact = re.sub(r"\s+", "-", (value or "").strip())
    return compact[:40] or "client"


def pick_template(product: str, business_type: str) -> str:
    """Portfolio for job seekers; business site for shops and professions."""
    if product == "portfolio":
        return "portfolio"
    text = f"{product} {business_type}".lower()
    if any(word in text for word in ("job", "freelance", "cv", "linkedin", "portfolio")):
        return "portfolio"
    return "business"


def _read_template(name: str) -> str:
    path = TEMPLATE_DIR / f"{name}.html"
    if not path.exists():
        raise FileNotFoundError(f"Missing demo template: {path}")
    return path.read_text(encoding="utf-8")


def build_demo(lead: dict) -> dict:
    """Render a demo folder and return slug + public URL.

    Why static HTML in Phase 0: Next.js templates come later. A filled
    HTML file is enough to trigger the endowment effect locally.
    """
    name = (lead.get("name") or "Client").strip()
    slug = slugify(name) or f"lead-{lead.get('id') or 'new'}"
    template = pick_template(lead.get("product") or "portfolio", lead.get("business_type") or "")
    html = _read_template(template)

    replacements = {
        "{{NAME}}": name,
        "{{HEADLINE}}": lead.get("profession") or lead.get("business_type") or "Professional",
        "{{BUSINESS}}": lead.get("business_type") or lead.get("profession") or "Services",
        "{{PHONE}}": lead.get("phone") or "",
        "{{CITY}}": lead.get("country") or "Tunisia",
        "{{ABOUT}}": lead.get("how_found")
        or "حضور رقمي واضح يساعد الناس على إيجاد هذا العمل والثقة به.",
        "{{BRAND}}": settings.brand_name,
    }
    for token, value in replacements.items():
        html = html.replace(token, value)

    dest = OUTPUT_DIR / slug
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "index.html").write_text(html, encoding="utf-8")
    url = f"{settings.demo_base_url.rstrip('/')}/demos/{slug}/"
    logger.info("Wrote demo %s", dest)
    return {"slug": slug, "url": url, "template": template, "path": str(dest)}
