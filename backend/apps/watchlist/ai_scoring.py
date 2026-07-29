"""AI relevance scoring for job postings (Pro feature).

Given a posting and a user's profile preferences, ask an LLM for a 0..1
relevance score. Runs AFTER the tier-2 keyword filter — this is the
second-pass "does this actually fit?" check that catches non-obvious matches
("Applied Scientist Intern" is relevant for someone wanting ML internships).

Design decisions:
- Only invoked for users on plans with `ai_relevance_scoring` AND with the
  per-user opt-in `ai_relevance_enabled` flag. Both must be true.
- Uses the user's `default_llm_provider` / `default_llm_model` — same
  provider setting the rest of the AI features use.
- JSON-only response, one field, so we can parse robustly.
- Fail-open: on any error, return None. Caller treats None as "don't gate
  the notification" so LLM outages don't silence alerts.
- Score is cached on the JobPosting; re-scoring is a caller decision.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

# Default cutoff: below this the posting is NOT surfaced to the user.
# Tuned to be forgiving — the tier-2 filter has already screened for basics.
RELEVANCE_THRESHOLD = 0.6

# Cap the amount of JD text we send. Keeps latency and cost predictable.
MAX_DESCRIPTION_CHARS = 1500

_SYSTEM_PROMPT = (
    "You rate how well a job posting matches a candidate's stated preferences. "
    "Output ONLY a JSON object with one key 'score' — a number from 0.0 (no fit) "
    "to 1.0 (perfect fit). No prose, no explanation."
)


def _build_prompt(*, title: str, location: str, description: str, prefs: dict) -> str:
    """Compose the user-facing prompt. Kept small and deterministic."""
    desc = (description or "").strip()[:MAX_DESCRIPTION_CHARS]
    lines = [
        "CANDIDATE PREFERENCES:",
        f"- Target roles / keywords: {', '.join(prefs.get('target_roles') or []) or '(any)'}",
        f"- Preferred job types: {', '.join(prefs.get('target_job_types') or []) or '(any)'}",
        f"- Preferred locations: {', '.join(prefs.get('preferred_locations') or []) or '(any)'}",
        f"- Excluded keywords: {', '.join(prefs.get('excluded_keywords') or []) or '(none)'}",
        "",
        "JOB POSTING:",
        f"Title: {title}",
        f"Location: {location or '(unspecified)'}",
        f"Description: {desc or '(none)'}",
        "",
        'Return: {"score": <0.0-1.0>}',
    ]
    return "\n".join(lines)


def _parse_score(text: str) -> float | None:
    """Extract score from the LLM's JSON response. Tolerates code fences."""
    if not text:
        return None
    # Strip common markdown code fences.
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: try to find the first {...} object.
        match = re.search(r"\{[^{}]*\}", cleaned)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    score = data.get("score")
    if not isinstance(score, int | float):
        return None
    # Clamp defensively — models sometimes return >1 or negatives.
    return max(0.0, min(1.0, float(score)))


def score_posting(*, posting, user) -> float | None:
    """Score a JobPosting for a user. Returns 0..1 or None on failure.

    Does NOT check plan gating or opt-in — the caller must. This lets the
    caller decide whether to call at all (avoids provider imports on the
    hot path when the user isn't eligible).
    """
    # Skip if the user has no preferences configured — scoring against a
    # blank spec gives useless numbers.
    profile = getattr(user, "profile", None)
    if profile is None:
        return None

    prefs = {
        "target_roles": list(profile.target_roles or []),
        "target_job_types": list(profile.target_job_types or []),
        "preferred_locations": list(profile.preferred_locations or []),
        "excluded_keywords": list(profile.excluded_keywords or []),
    }
    if not any(prefs.values()):
        return None

    provider_name = profile.default_llm_provider or "gemini"
    model_name = profile.default_llm_model or None

    # Import lazily so this module stays importable in environments without
    # LLM SDKs installed (e.g. during migrations).
    from llm_providers.registry import get_llm_provider

    try:
        provider = get_llm_provider(provider_name, model_name)
        prompt = _build_prompt(
            title=posting.title,
            location=posting.location,
            description=posting.description_text,
            prefs=prefs,
        )
        response = asyncio.run(provider.generate(prompt, context={"system": _SYSTEM_PROMPT}))
    except Exception as exc:
        # Fail-open. Don't gate notifications on a flaky LLM.
        logger.warning(f"AI relevance scoring failed for posting {posting.id}: {exc}")
        return None

    return _parse_score(response.text)


def should_score(user) -> bool:
    """Gate check: user opted in AND (payments off OR plan supports it)."""
    profile = getattr(user, "profile", None)
    if profile is None or not profile.ai_relevance_enabled:
        return False

    # PAYMENTS_ENABLED=False unlocks paywalled features for testing.
    if not getattr(settings, "PAYMENTS_ENABLED", False):
        return True

    from apps.billing.permissions import get_user_limits

    return bool(get_user_limits(user).get("ai_relevance_scoring", False))
