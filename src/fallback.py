"""Deterministic conversation engine for local testing without an API key."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from src.config import settings
from src.intent import asks_price


class FallbackChatModel:
    """Mimics a LangChain chat model so the graph stays provider-agnostic.

    Used only when no LLM key is present. Responses follow the 13-block
    rules: short, one question at a time, respond-first, no AI-speak.
    """

    def invoke(self, messages: list, **_: Any) -> AIMessage:
        system = ""
        last_user = ""
        for msg in messages:
            role = getattr(msg, "type", None)
            content = str(getattr(msg, "content", "") or "")
            if role == "system":
                system = content
            if role == "human":
                last_user = content
        return AIMessage(content=_compose_reply(system, last_user))


def _reply_language(system: str) -> str:
    if "French" in system:
        return "fr"
    if "English" in system:
        return "en"
    return "ar"


def _field(system: str, label: str) -> str:
    for line in system.splitlines():
        if line.strip().startswith(label):
            return line.split(":", 1)[-1].strip()
    return ""


def _compose_reply(system: str, last_user: str) -> str:
    lang = _reply_language(system)
    name = _field(system, "Client name:")
    if name in {"the contact", "unknown", ""}:
        name = ""
    profession = _field(system, "Business / profession:")
    has_site = _field(system, "Has a website already:")
    how_found = _field(system, "How people find them:")
    phase = _field(system, "Current phase:")
    demo = ""
    if "Take a look:" in system:
        for token in system.split():
            if token.startswith("http"):
                demo = token.rstrip("].")
                break

    if asks_price(last_user):
        return _price_line(lang)

    if "not yet known" in profession or not profession:
        return _ask_profession(lang, name, last_user)
    if has_site in {"unknown", ""}:
        return _ask_website(lang, last_user)
    if how_found in {"unknown", ""}:
        return _ask_discovery(lang, last_user)
    if phase == "demo" and not demo:
        return _ask_demo_permission(lang, last_user)
    if demo:
        return _present_demo(lang, demo)
    if phase == "closing":
        return _close(lang)
    return _ask_demo_permission(lang, last_user)


def _ack(lang: str, last_user: str) -> str:
    if not last_user.strip():
        return ""
    if lang == "fr":
        return "Merci, c'est noté. "
    if lang == "en":
        return "Got it. "
    return "تمام، سجلت. "


def _ask_profession(lang: str, name: str, last_user: str) -> str:
    hello = f"{name}، " if name else ""
    if lang == "fr":
        return f"Bonjour {name or ''}. Vous faites quoi comme métier ?".strip()
    if lang == "en":
        return f"Hi {name or ''}. What do you do for work?".strip()
    if last_user:
        return f"{_ack(lang, last_user)}شنوة مجال عملك أو مهنتك؟"
    return f"مرحبا {hello}أنا مساعد السيد {settings.founder_name}. عندك دقيقتين؟ شنوة تخدم؟"


def _ask_website(lang: str, last_user: str) -> str:
    if lang == "fr":
        return f"{_ack(lang, last_user)}Vous avez déjà un site web ?"
    if lang == "en":
        return f"{_ack(lang, last_user)}Do you currently have a website?"
    return f"{_ack(lang, last_user)}عندك موقع أو حضور رقمي حاليا؟"


def _ask_discovery(lang: str, last_user: str) -> str:
    if lang == "fr":
        return f"{_ack(lang, last_user)}Aujourd'hui, comment les gens vous trouvent ?"
    if lang == "en":
        return f"{_ack(lang, last_user)}How do people currently find you?"
    return f"{_ack(lang, last_user)}الناس كيفاش يلقاوك اليوم؟"


def _ask_demo_permission(lang: str, last_user: str) -> str:
    if lang == "fr":
        return f"{_ack(lang, last_user)}On peut préparer une première version de votre présence en ligne. Vous voulez la voir ?"
    if lang == "en":
        return f"{_ack(lang, last_user)}We can prepare a first version of your online presence. Want to see it?"
    return f"{_ack(lang, last_user)}نجموا نحضّروا نسخة أولى لحضورك الرقمي. تحب تشوفها؟"


def _present_demo(lang: str, url: str) -> str:
    if lang == "fr":
        return f"On a préparé une première version à partir de ce que vous avez dit. Jetez un œil : {url} Vous voulez changer quelque chose ?"
    if lang == "en":
        return (
            f"We prepared an initial version based on what you told us. "
            f"Take a look: {url} Want to change anything?"
        )
    return f"حضّرنا نسخة أولى حسب اللي قلت لنا. شوف هنا: {url} تحب تبدل حاجة أو تزيد تفاصيل؟"


def _close(lang: str) -> str:
    if lang == "fr":
        return "Le site est prêt. La version complète avec votre nom coûte 12 $/mois. Tout se gère par message."
    if lang == "en":
        return "Your site is ready. The full version under your name is 12 $/month, managed by message."
    return "الموقع جاهز. النسخة الكاملة باسمك بـ 12 دولار في الشهر، وكل تعديل برسالة."


def _price_line(lang: str) -> str:
    if lang == "fr":
        return "Le portfolio est entre 10 et 15 $/mois. Pas de frais cachés. On confirme après la démo."
    if lang == "en":
        return "Portfolio is 10–15 $/month. Fair pricing, no hidden fees. We confirm after the demo."
    return "البورتفوليو بين 10 و 15 دولار في الشهر. سعر واضح، والتأكيد بعد ما تشوف الديمو."
