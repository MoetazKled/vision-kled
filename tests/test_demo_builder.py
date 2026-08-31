from src.demo_builder import pick_template, slugify
from src.extract import heuristic_extract


def test_slugify_ascii() -> None:
    assert slugify("Sara Ben Ali") == "sara-ben-ali"


def test_pick_portfolio() -> None:
    assert pick_template("portfolio", "lawyer") == "portfolio"
    assert pick_template("business", "restaurant") == "business"


def test_heuristic_fills_one_slot() -> None:
    lead = heuristic_extract({}, "محامية", "شنوة تخدم؟")
    assert lead["profession"] == "محامية"
    lead = heuristic_extract(lead, "لا", "عندك موقع؟")
    assert lead["has_website"] == "no"
