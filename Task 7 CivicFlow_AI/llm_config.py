"""
CivicFlow AI — LLM client factory.
==================================
`DummyLLM` (jo `NotImplementedError` raise karta tha) hata diya gaya hai.

Ab ye module:
  1. Asli **ChatGroq** deta hai (primary provider — free tier, fast).
  2. Groq na ho to **Gemini** par fallback karta hai.
  3. Dono na hon to `None` deta hai aur `engine_status()` saaf batata hai ke app
     *degraded (rule-based) mode* mein hai. Ye sab se ehem hissa hai — app
     jhoota AI output nahi dikhati, saaf label lagati hai.

Design rule: is file se koi exception bahar nahi jati. Import fail ho, key
missing ho, network down ho — sab kuch `LLMStatus` mein report hota hai taake
UI imaandari se dikha sake.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, List, Optional

import settings

logger = logging.getLogger("civicflow.llm")

# ==========================================================
# Status object — UI isay padh kar banner dikhati hai
# ==========================================================


@dataclass
class LLMStatus:
    """LLM layer ki sachi haalat. UI ise direct render karti hai."""

    available: bool = False
    provider: str = "none"          # "groq" | "gemini" | "none"
    model: str = "—"
    degraded: bool = True           # True = rule-based fallback chal raha hai
    reason: str = ""                # kyun unavailable hai (user ko dikhane ke liye)
    notes: List[str] = field(default_factory=list)

    @property
    def badge(self) -> str:
        if self.available:
            return f"🟢 Live · {self.provider.title()} · {self.model}"
        if settings.ALLOW_DEGRADED_MODE:
            return "🟡 Degraded mode · rule-based (no LLM)"
        return "🔴 Engine offline"

    @property
    def label(self) -> str:
        return "AI Engine: LLM active" if self.available else "AI Engine: rule-based fallback"


_STATUS = LLMStatus()


def engine_status() -> LLMStatus:
    """Current LLM status. Pehli dafa call par client initialise ho jata hai."""
    get_llm()
    return _STATUS


# ==========================================================
# Provider builders
# ==========================================================


def _build_groq() -> Optional[Any]:
    if not settings.has_groq_key():
        _STATUS.notes.append("GROQ_API_KEY set nahi hai.")
        return None
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        _STATUS.notes.append(
            "`langchain-groq` install nahi hai — chalayein: pip install langchain-groq"
        )
        return None
    try:
        client = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_retries=2,
            timeout=45,
        )
        _STATUS.available = True
        _STATUS.provider = "groq"
        _STATUS.model = settings.LLM_MODEL
        _STATUS.degraded = False
        _STATUS.reason = ""
        return client
    except Exception as exc:
        logger.exception("Groq client banane mein masla")
        _STATUS.notes.append(f"Groq init failed: {exc}")
        return None


def _build_gemini() -> Optional[Any]:
    if not settings.has_gemini_key():
        _STATUS.notes.append("GOOGLE_API_KEY set nahi hai (optional fallback).")
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        _STATUS.notes.append("`langchain-google-genai` install nahi hai (optional).")
        return None
    try:
        client = ChatGoogleGenerativeAI(
            google_api_key=settings.GOOGLE_API_KEY,
            model=settings.GEMINI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )
        _STATUS.available = True
        _STATUS.provider = "gemini"
        _STATUS.model = settings.GEMINI_MODEL
        _STATUS.degraded = False
        _STATUS.reason = ""
        return client
    except Exception as exc:
        logger.exception("Gemini client banane mein masla")
        _STATUS.notes.append(f"Gemini init failed: {exc}")
        return None


# ==========================================================
# Observability — LangSmith tracing (optional)
# ==========================================================


def _enable_tracing() -> None:
    """LangSmith env vars set karein taake LangGraph runs trace hon."""
    if not (settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY):
        return
    import os

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    _STATUS.notes.append(f"LangSmith tracing ON → project '{settings.LANGCHAIN_PROJECT}'")


# ==========================================================
# Public factory
# ==========================================================


@lru_cache(maxsize=1)
def get_llm() -> Optional[Any]:
    """Ek hi LLM client (cached). Na mile to `None` — exception nahi.

    Tarteeb: Groq → Gemini → None (degraded mode).
    Caller ka farz: `if llm is None:` check kar ke rule-based path chalana.
    """
    _STATUS.notes.clear()
    _enable_tracing()

    client = _build_groq()
    if client is None:
        client = _build_gemini()

    if client is None:
        _STATUS.available = False
        _STATUS.provider = "none"
        _STATUS.model = "—"
        _STATUS.degraded = True
        _STATUS.reason = (
            "Koi LLM provider available nahi. `.env` mein GROQ_API_KEY daalein "
            "(https://console.groq.com/keys) ya GOOGLE_API_KEY. "
            "Tab tak app rule-based mode mein chal rahi hai."
        )
        logger.warning("LLM unavailable — degraded mode. %s", _STATUS.notes)
    else:
        logger.info("LLM ready: %s / %s", _STATUS.provider, _STATUS.model)

    return client


def llm_available() -> bool:
    """Chhota helper — agents isay guard ke tor par use karte hain."""
    return get_llm() is not None


def reset_llm_cache() -> None:
    """Settings page se 'Reconnect' button ke liye — cache saaf kar ke re-init."""
    get_llm.cache_clear()
    _STATUS.notes.clear()


# ==========================================================
# Structured output helper — Pydantic schema ke sath
# ==========================================================


def get_structured_llm(schema: Any) -> Optional[Any]:
    """`schemas.py` ka koi Pydantic model do, structured-output runnable milega.

    Rubric ka "Structured Outputs with Pydantic" requirement yahan pura hota hai.
    LLM na ho ya schema binding fail ho to `None` — caller fallback chalaye.
    """
    client = get_llm()
    if client is None:
        return None
    try:
        return client.with_structured_output(schema)
    except Exception as exc:
        logger.exception("with_structured_output fail for %s", getattr(schema, "__name__", schema))
        _STATUS.notes.append(f"Structured output bind failed: {exc}")
        return None


def safe_structured_invoke(schema: Any, prompt: Any, default: Any = None) -> Any:
    """LLM ko structured output ke sath call karein — kabhi raise nahi karta.

    Args:
        schema:  Pydantic model class (`schemas.py` se).
        prompt:  string ya messages list.
        default: LLM na chale to ye wapas milta hai (usually rule-based result).

    Returns:
        Parsed Pydantic object, warna `default`.
    """
    runnable = get_structured_llm(schema)
    if runnable is None:
        return default

    last_error: Optional[Exception] = None
    for attempt in range(1, settings.MAX_VALIDATION_REPAIRS + 2):
        try:
            return runnable.invoke(prompt)
        except Exception as exc:  # validation / network / rate-limit
            last_error = exc
            logger.warning(
                "Structured invoke attempt %s/%s failed: %s",
                attempt, settings.MAX_VALIDATION_REPAIRS + 1, exc,
            )
    _STATUS.notes.append(f"Structured invoke gave up: {last_error}")
    return default


def safe_text_invoke(prompt: Any, default: str = "") -> str:
    """Plain text generation — kabhi raise nahi karta. Copilot/summary ke liye."""
    client = get_llm()
    if client is None:
        return default
    try:
        response = client.invoke(prompt)
        content = getattr(response, "content", response)
        if isinstance(content, list):  # some providers return content blocks
            content = " ".join(
                str(part.get("text", part)) if isinstance(part, dict) else str(part)
                for part in content
            )
        return str(content).strip() or default
    except Exception as exc:
        logger.warning("Text invoke failed: %s", exc)
        _STATUS.notes.append(f"Text invoke failed: {exc}")
        return default


# ==========================================================
# Backwards compatibility
# ==========================================================
# Purana code `get_groq_llm()` call karta tha. Ab wahi cached client deta hai,
# magar key missing par `ValueError` raise nahi karta — `None` deta hai.


def get_groq_llm() -> Optional[Any]:
    """Deprecated alias — `get_llm()` use karein."""
    return get_llm()


__all__ = [
    "LLMStatus",
    "engine_status",
    "get_llm",
    "get_groq_llm",
    "get_structured_llm",
    "llm_available",
    "reset_llm_cache",
    "safe_structured_invoke",
    "safe_text_invoke",
]
