from src.graph.graph import run_turn


def test_first_turn_asks_a_question() -> None:
    result = run_turn(
        user_text="مرحبا",
        lead={"name": "سارة", "phone": "+21620123456", "product": "portfolio"},
        history=[],
    )
    assert result["language"] == "ar"
    assert result["last_assistant"]
    assert "؟" in result["last_assistant"] or "?" in result["last_assistant"]
