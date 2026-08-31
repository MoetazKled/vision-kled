"""Language detection from phone country code (Agent 7)."""

from __future__ import annotations

import re

# Prefixes documented in Vision Kled §3.3 and §4.7.
ARABIC_PREFIXES = ("216", "212", "213", "218", "20", "966", "971", "974", "973", "965")
FRENCH_PREFIXES = ("33", "32", "41", "352")


def normalize_phone(phone: str) -> str:
    """Keep digits only so +216 93 160 585 and 00216... match the same prefix."""
    return re.sub(r"\D", "", phone or "")


def detect_language(phone: str, fallback: str = "en") -> str:
    """Return ar, fr, or en from a phone number.

    Unknown / empty numbers fall back to English, as specified.
    """
    digits = normalize_phone(phone)
    if digits.startswith("00"):
        digits = digits[2:]

    for prefix in sorted(ARABIC_PREFIXES, key=len, reverse=True):
        if digits.startswith(prefix):
            return "ar"
    for prefix in sorted(FRENCH_PREFIXES, key=len, reverse=True):
        if digits.startswith(prefix):
            return "fr"
    if digits:
        return "en"
    return fallback


def language_label(code: str) -> str:
    """Human-readable language name used in prompts."""
    return {"ar": "Arabic", "fr": "French", "en": "English"}.get(code, "English")
