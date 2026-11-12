"""Chooses how to answer: the AI agent if available, otherwise the closest policy passage."""
import logging
import re

from app import config, retrieval

log = logging.getLogger("policy-assistant")


def _explain(exc: Exception) -> str:
    """A short, honest reason for the user (the full error is in the server log)."""
    text = f"{type(exc).__name__} {exc}".lower()
    if "429" in text or "resource_exhausted" in text or "quota" in text or "rate limit" in text:
        return "The AI service is busy (free-tier rate limit). Try again in a minute."
    if "api key" in text or "api_key" in text or "permission" in text or "403" in text or "401" in text:
        return "The AI service rejected the API key."
    if "404" in text or "not found" in text:
        return "The AI model name was not found. Check GEMINI_MODEL."
    if "timeout" in text or "timed out" in text or "connect" in text:
        return "The AI service could not be reached."
    return f"The AI service had a problem ({type(exc).__name__})."


def _plain_text(passage: str) -> str:
    """Show policy text as written. Markdown would turn '3. Heading' into a list that starts
    at 3 and glues lines together, so escape the numbers and put each line in its own paragraph."""
    lines = [ln.strip() for ln in passage.splitlines() if ln.strip()]
    return "\n\n".join(re.sub(r"^(\d+)\.", r"\1\\.", ln) for ln in lines)


def _excerpt_fallback(question: str, reason: str) -> tuple[str, list[dict]]:
    hits = retrieval.search(question, k=3)
    if not hits:
        return "No policy documents are available yet. Please ask an admin to upload some.", []

    top = hits[0]
    try:  # show just the section that matches the question, not the whole chunk
        from app.agent import _best_passage

        passage = _best_passage(top["text"], question)
    except Exception:
        passage = top["text"]

    answer = (
        f"{reason} Showing the closest policy passage instead, from {top['source']}:\n\n"
        f"{_plain_text(passage)}"
    )
    source = {"source": top["source"], "page": top["page"], "score": top["score"], "snippet": passage}
    return answer, [source]  # cite only the passage we actually show


def answer_question(question: str, history: list[dict], user: dict) -> tuple[str, list[dict]]:
    if not config.GEMINI_API_KEY:
        return _excerpt_fallback(question, "AI answers are switched off (no GEMINI_API_KEY is set).")
    try:
        from app.agent import run_agent

        return run_agent(question, history, user)
    except Exception as exc:  # quota, bad model name, network ...  never crash the chat
        log.exception("Agent failed")
        return _excerpt_fallback(question, _explain(exc))
