"""Optional OpenRouter phrasing. The model rewords a fixed, state-derived reply; it never chooses actions."""

import json
import os
import re
import urllib.request

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-sonnet-5.5"
SYSTEM = (
    "You are Habilin, an estate case assistant. Rewrite FACTS as a short, warm reply (at most 3 sentences) to the "
    "user's message. Match the user's language: English, or Taglish if they wrote Taglish. Use only information in "
    "FACTS. Do not add numbers, dates, names, emails, links, payees or promises. Do not say an action happened unless "
    "FACTS say so. Never ask for or mention one-time codes. Plain text only."
)


def _tokens(pattern, text):
    return {t.replace(",", "").rstrip(".") for t in re.findall(pattern, text)}


RISKY = re.compile(r"\b(codes?|otp|pins?|passwords?|personal|transfers?|send|gcash|account numbers?|tokens?)\b", re.I)


def _grounded(text, facts):
    """Reject a reply that mentions codes or money movement, or adds any number, email or link absent from the facts."""
    numbers, contacts = r"\d[\d,.]*", r"[\w.+-]+@[\w-]+\.[\w.]+|https?://\S+"
    # A rewording never needs to mention codes or money movement; the fixed reply does that.
    if RISKY.search(text):
        return False
    return _tokens(numbers, text) <= _tokens(numbers, facts) and _tokens(contacts, text) <= _tokens(contacts, facts)


def phrase(facts, user_text):
    """Return (reply, model). Falls back to the fixed facts when unconfigured, unavailable or ungrounded."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return facts, None
    model = os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
    payload = {"model": model, "max_tokens": 220, "temperature": 0.3, "messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps({"FACTS": facts, "user_message": user_text})}]}
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(), headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json", "X-Title": "Habilin"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            text = json.load(response)["choices"][0]["message"]["content"].strip()
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError):
        return facts, None
    if not text or len(text) > 700 or not _grounded(text, facts):
        return facts, None
    return text, model
