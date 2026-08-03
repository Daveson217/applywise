"""Auto-detect ATS by probing each provider's public API with a slugified name.

Fallback for when the user gives us a company name but no ATS-recognizable URL
(e.g. they pasted careers.stripe.com instead of boards.greenhouse.io/stripe).

Approach:
- Slugify the name into a few likely candidates.
- For each ATS in priority order, HEAD/GET the job-board endpoint for that slug.
- First 200 wins. Return provider + slug + canonical URL.

Guarantees:
- Bounded work: at most len(SLUG_CANDIDATES) * len(ATS_PROBES) HTTP calls,
  short circuits on first hit.
- Short timeout per call (3s). Sequential to avoid burning a hole in latency
  when things are healthy.
- Only requests to fixed, well-known ATS domains — no SSRF surface.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Per-provider: (name, board-page URL template, API check URL template).
# board_url is what we save to careers_url and show to the user.
# probe_url is what we HEAD/GET to test whether the slug exists.
_PROBES: list[tuple[str, str, str]] = [
    (
        "greenhouse",
        "https://boards.greenhouse.io/{slug}",
        "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    ),
    (
        "lever",
        "https://jobs.lever.co/{slug}",
        "https://api.lever.co/v0/postings/{slug}",
    ),
    (
        "ashby",
        "https://jobs.ashbyhq.com/{slug}",
        "https://api.ashbyhq.com/posting-api/job-board/{slug}",
    ),
    (
        "workable",
        "https://apply.workable.com/{slug}",
        "https://apply.workable.com/api/v3/accounts/{slug}/jobs",
    ),
    (
        "smartrecruiters",
        "https://careers.smartrecruiters.com/{slug}",
        "https://api.smartrecruiters.com/v1/companies/{slug}/postings",
    ),
]

# Words to strip when generating slug candidates from company names.
_STOP_SUFFIXES = re.compile(
    r"\b(inc|incorporated|corp|corporation|llc|ltd|limited|technologies|"
    r"tech|labs|ai|the|and|&|co)\b",
    re.IGNORECASE,
)

_PROBE_TIMEOUT_SECONDS = 3.0


@dataclass
class ProbeResult:
    provider: str
    slug: str
    board_url: str


def _slug_candidates(name: str) -> list[str]:
    """Generate ordered candidate slugs from a company name.

    Priority: cleanest slug first (all lowercase, no suffixes, no punctuation).
    Then variants with suffixes stripped, hyphens vs. no-separator, etc.
    De-duplicated in order.
    """
    if not name:
        return []

    base = name.strip().lower()
    stripped = _STOP_SUFFIXES.sub("", base).strip()

    variants: list[str] = []
    for candidate in (stripped, base):
        # Replace anything that's not alnum with a hyphen, collapse repeats.
        s = re.sub(r"[^a-z0-9]+", "-", candidate).strip("-")
        if s:
            variants.append(s)
            # Also try the concatenated form (no hyphens) — many companies use it
            variants.append(s.replace("-", ""))

    # De-duplicate, preserve order, drop very short/long strings.
    seen: set[str] = set()
    result: list[str] = []
    for v in variants:
        if 2 <= len(v) <= 60 and v not in seen:
            seen.add(v)
            result.append(v)
    return result


def _probe_slug(client: httpx.Client, slug: str) -> ProbeResult | None:
    """Try each ATS for one slug. Returns the first hit or None."""
    for provider, board_tpl, probe_tpl in _PROBES:
        try:
            resp = client.get(probe_tpl.format(slug=slug))
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            logger.debug(f"Probe error for {provider}/{slug}: {exc}")
            continue
        if resp.status_code == 200:
            return ProbeResult(
                provider=provider,
                slug=slug,
                board_url=board_tpl.format(slug=slug),
            )
    return None


def probe_by_name(name: str) -> ProbeResult | None:
    """Given a company name, try to find its ATS across known providers.

    Returns the first successful (provider, slug, canonical URL) or None.
    Safe to call synchronously — total worst-case time is bounded by
    len(candidates) * len(providers) * PROBE_TIMEOUT_SECONDS.
    """
    candidates = _slug_candidates(name)
    if not candidates:
        return None

    with httpx.Client(
        timeout=_PROBE_TIMEOUT_SECONDS,
        follow_redirects=False,
        headers={"User-Agent": "Applywise-Watchlist/1.0"},
    ) as client:
        for slug in candidates:
            result = _probe_slug(client, slug)
            if result:
                return result
    return None
