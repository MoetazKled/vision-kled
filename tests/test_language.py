from src.language import detect_language, language_label, normalize_phone


def test_tunisia_is_arabic() -> None:
    assert detect_language("+216 20 123 456") == "ar"


def test_france_is_french() -> None:
    assert detect_language("+33 6 15 14 57 65") == "fr"


def test_unknown_defaults_to_english() -> None:
    assert detect_language("+44 7700 900123") == "en"


def test_empty_uses_fallback() -> None:
    assert detect_language("", fallback="ar") == "ar"


def test_normalize_keeps_digits() -> None:
    assert normalize_phone("+216-20-12") == "2162012"


def test_language_label() -> None:
    assert language_label("ar") == "Arabic"
