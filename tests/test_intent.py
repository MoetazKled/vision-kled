from src.intent import is_opt_out, parse_website_answer, wants_demo, wants_subscription


def test_demo_requires_ready_lead() -> None:
    assert wants_demo("نعم", ready_for_demo=False, has_demo=False) is False
    assert wants_demo("نعم", ready_for_demo=True, has_demo=False) is True
    assert wants_demo("نعم", ready_for_demo=True, has_demo=True) is False


def test_demo_not_from_opening_yes() -> None:
    assert (
        wants_demo(
            "أيوا عندي دقيقتين",
            ready_for_demo=True,
            has_demo=False,
            last_assistant="عندك دقيقتين؟",
        )
        is False
    )
    assert (
        wants_demo(
            "نعم",
            ready_for_demo=True,
            has_demo=False,
            last_assistant="تحب تشوف النسخة؟",
        )
        is True
    )


def test_opt_out() -> None:
    assert is_opt_out("توقف من فضلك") is True
    assert is_opt_out("stop") is True
    assert is_opt_out("ما زلت مهتما") is False


def test_website_answers() -> None:
    assert parse_website_answer("لا ما عنديش") == "no"
    assert parse_website_answer("نعم عندي") == "yes"


def test_subscription_intent() -> None:
    assert wants_subscription("نبدأ، أشترك") is True
