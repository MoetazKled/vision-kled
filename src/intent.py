"""Detect client intent from a WhatsApp-style message.

Why a dedicated module: the graph must not treat every "نعم" as demo
consent. Affirmatives only count after the three discovery questions are filled.
"""

from __future__ import annotations

import re

_AFFIRM = re.compile(
    r"\b(yes|yeah|yep|ok|okay|oui|ouais|okey|d['’]accord)\b|"
    r"(نعم|أيوا|ايوا|أيوه|موافق|ماشي|حاضر|شاهد|شوف|الديمو|الموقع)",
    re.IGNORECASE,
)
_NEGATE = re.compile(
    r"\b(no|nope|not now|later|non|pas maintenant)\b|"
    r"(لا|مش الآن|مو الآن|بعدين|لاحق)",
    re.IGNORECASE,
)
_OPT_OUT = re.compile(
    r"\b(stop|unsubscribe|opt[ -]?out|remove me)\b|"
    r"(توقف|ألغني|الغني|لا تراسلني|مش مهتم|غير مهتم)",
    re.IGNORECASE,
)
_PRICE = re.compile(
    r"\b(price|cost|how much|tarif|prix)\b|(السعر|بقداش|بكم|الثمن)",
    re.IGNORECASE,
)
_CLOSE = re.compile(
    r"\b(subscribe|subscribe|take it|i want it|deal)\b|"
    r"(أشترك|اشترك|أريدها|آخذها|نبدأ|خلينا نثبت)",
    re.IGNORECASE,
)
_YES_WEBSITE = re.compile(
    r"\b(yes|oui|i have|j['’]ai)\b|(نعم|عندي|يوجد|موجود)",
    re.IGNORECASE,
)
_NO_WEBSITE = re.compile(
    r"\b(no|non|i don['’]?t|none)\b|(لا|ما عنديش|ماعنديش|بدون|ما فيش)",
    re.IGNORECASE,
)


def is_affirmative(text: str) -> bool:
    """True when the client clearly agrees."""
    return bool(_AFFIRM.search(text or "")) and not bool(_NEGATE.search(text or ""))


def is_opt_out(text: str) -> bool:
    """True when the client asks to stop being contacted."""
    return bool(_OPT_OUT.search(text or ""))


def asks_price(text: str) -> bool:
    """True when the client asks about pricing."""
    return bool(_PRICE.search(text or ""))


def wants_subscription(text: str) -> bool:
    """True when the client accepts the offer after seeing the demo."""
    return bool(_CLOSE.search(text or ""))


def parse_website_answer(text: str) -> str:
    """Map a free-text reply to yes/no/empty for has_website."""
    if _NO_WEBSITE.search(text or ""):
        return "no"
    if _YES_WEBSITE.search(text or ""):
        return "yes"
    return ""


def wants_demo(
    user_text: str,
    *,
    ready_for_demo: bool,
    has_demo: bool,
    last_assistant: str = "",
) -> bool:
    """HITL gate: demo is built only after discovery is complete and they agree.

    A plain "نعم" to "عندك دقيقتين؟" must not trigger a demo.
    """
    if has_demo or not ready_for_demo:
        return False
    if last_assistant:
        asked = any(
            word in last_assistant.lower()
            for word in ("ديمو", "نسخة", "demo", "présence", "voir", "حضور رقم", "online presence")
        )
        if not asked:
            return False
    return is_affirmative(user_text)
