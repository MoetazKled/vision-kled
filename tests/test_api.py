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
