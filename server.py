"""FastAPI: serve generated demos and accept manual lead injection."""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db, init_db
from src.demo_builder import build_demo
from src.language import detect_language
from src.memory import lead_to_dict, upsert_lead
from src.models import DemoSite, Lead

ROOT = Path(__file__).resolve().parent
DEMOS = ROOT / "demos_output"
DEMOS.mkdir(exist_ok=True)

app = FastAPI(title="Vision Kled API", version="0.1.0")
app.mount("/demos", StaticFiles(directory=DEMOS, html=True), name="demos")


class LeadIn(BaseModel):
    name: str = Field(..., min_length=1)
    phone: str = ""
    business_type: str = ""
    profession: str = ""
    product: str = "portfolio"
    country: str = ""


class LeadOut(BaseModel):
    id: int
    name: str
    phone: str
    language: str
    product: str
    status: str


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "brand": settings.brand_name}


@app.post("/api/v1/leads", response_model=LeadOut)
def create_lead(payload: LeadIn, db: Session = Depends(get_db)) -> LeadOut:
    """Admin-only in Phase 0: paste a contact instead of scraping."""
    language = detect_language(payload.phone, fallback="ar")
    lead = upsert_lead(
        db,
        {
            **payload.model_dump(),
            "language": language,
            "status": "new",
        },
    )
    return LeadOut(
        id=lead.id,
        name=lead.name,
        phone=lead.phone,
        language=lead.language,
        product=lead.product,
        status=lead.status,
    )


@app.get("/api/v1/leads")
def list_leads(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Lead).order_by(Lead.id.desc()).all()
    return [lead_to_dict(row) for row in rows]


@app.post("/api/v1/leads/{lead_id}/demo")
def generate_demo(lead_id: int, db: Session = Depends(get_db)) -> dict:
    lead = db.query(Lead).filter_by(id=lead_id).one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    result = build_demo(lead_to_dict(lead))
    demo = DemoSite(
        lead_id=lead.id,
        slug=result["slug"],
        template=result["template"],
        url=result["url"],
    )
    db.add(demo)
    lead.status = "demo_ready"
    db.commit()
    return result
