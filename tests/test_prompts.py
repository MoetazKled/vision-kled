from src.prompts import build_system_prompt


def test_prompt_contains_all_thirteen_blocks() -> None:
    prompt = build_system_prompt(
        language="ar",
        lead={"name": "Sami", "phone": "+216"},
        phase="outreach",
        product="portfolio",
    )
    for index in range(1, 14):
        assert f"[{index} " in prompt
    assert "Sami" in prompt
    assert "Arabic" in prompt
