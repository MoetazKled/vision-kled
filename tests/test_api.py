from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_products_catalog() -> None:
    response = client.get("/api/products")
    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()}
    assert {"portfolio", "business", "bac"} <= slugs


def test_trial_lead_and_delete() -> None:
    created = client.post("/api/leads/trial")
    assert created.status_code == 200
    lead_id = created.json()["id"]
    listed = client.get("/api/leads")
    assert any(row["id"] == lead_id for row in listed.json())
    deleted = client.delete(f"/api/leads/{lead_id}")
    assert deleted.status_code == 200


def test_demo_escapes_html() -> None:
    from src.demo_builder import OUTPUT_DIR, build_demo

    result = build_demo(
        {
            "id": 99,
            "name": "Test<script>alert(1)</script>",
            "profession": "Dev",
            "product": "portfolio",
            "phone": "+216",
            "country": "Tunisia",
        }
    )
    html = (OUTPUT_DIR / result["slug"] / "index.html").read_text(encoding="utf-8")
    assert "<script>" not in html
    assert "Test&lt;script&gt;" in html
