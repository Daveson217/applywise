"""Tier-2 fuzzy/synonym matching for watchlist rules.

Given a job posting and a rule, decides whether the posting should trigger
a notification. Pure functions; easy to test in isolation.

Design:
- Word-boundary matching (regex \\b) so "ai" doesn't match "paid".
- Synonym expansion for common tech and job-type terms — user types "ML",
  we also look for "machine learning", "ai/ml", etc.
- Job-type inference from the title (e.g. "SWE Intern" → {"internship"}).
- Exclusions win: if any excluded keyword matches, we skip the posting even
  if the positive keywords also matched.
"""

from __future__ import annotations

import re

# Canonical form → aliases that all mean the same thing.
# Matching is symmetric: any alias in the rule expands to the whole group.
# Keep lowercase; matching is case-insensitive.
_SYNONYM_GROUPS: list[set[str]] = [
    # Roles
    {"swe", "software engineer", "software developer", "sde"},
    {"ml", "machine learning", "ai/ml", "ml engineer"},
    {"ai", "artificial intelligence"},
    {"data scientist", "ds"},
    {"data engineer", "de"},
    {"data analyst", "analytics"},
    {"backend", "back-end", "back end"},
    {"frontend", "front-end", "front end"},
    {"full stack", "fullstack", "full-stack"},
    {"devops", "sre", "site reliability", "platform engineer"},
    {"product manager", "pm", "product management"},
    {"ux", "user experience"},
    {"qa", "quality assurance", "test engineer", "sdet"},
    # Job types
    {"intern", "internship", "co-op", "coop", "summer 2026", "summer 2025"},
    {"new grad", "new-grad", "entry level", "entry-level", "university grad"},
    {"contract", "contractor", "contract-to-hire"},
    # Locations
    {"remote", "fully remote", "work from home", "wfh"},
    {"hybrid"},
    {"onsite", "on-site", "in office", "in-office"},
]

# Build lookup: token → set of all synonyms in its group.
_SYNONYM_INDEX: dict[str, set[str]] = {}
for group in _SYNONYM_GROUPS:
    for term in group:
        _SYNONYM_INDEX.setdefault(term, set()).update(group)


# Common job-type patterns inferred directly from title text.
# We check these against the user's target_job_types filter.
_JOB_TYPE_PATTERNS: dict[str, re.Pattern] = {
    "internship": re.compile(r"\b(intern|internship|co-?op|summer\s+20\d{2})\b", re.I),
    "new_grad": re.compile(r"\b(new[-\s]?grad|entry[-\s]?level|university\s+grad)\b", re.I),
    "contract": re.compile(r"\b(contract(or)?|contract-to-hire)\b", re.I),
    "full_time": re.compile(r"\b(full[-\s]?time|permanent|fte)\b", re.I),
    "part_time": re.compile(r"\b(part[-\s]?time)\b", re.I),
}

# ─── US location awareness ───────────────────────────────────────────────
# A country filter like "United States" must match postings whose location
# reads "Mountain View, CA" or "Remote - US" — the literal string "united
# states" almost never appears. We detect US-ness via state names/abbrs.

# Terms a user might type to mean "anywhere in the US".
_US_COUNTRY_TERMS = {"united states", "usa", "us", "u.s.", "u.s.a.", "america"}

_US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
    "district of columbia", "washington dc", "washington d.c.",
}

_US_STATE_ABBRS = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
    "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok",
    "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy", "dc",
}

# Regexes built once. State abbrs need word boundaries so "ca" matches
# "San Jose, CA" but not "Canada" or "campus".
_US_COUNTRY_RE = re.compile(
    r"\b(united states|u\.?s\.?a\.?|u\.?s\.?|america)\b", re.I
)
_US_STATE_NAME_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in _US_STATE_NAMES) + r")\b", re.I
)
_US_STATE_ABBR_RE = re.compile(
    r"\b(" + "|".join(_US_STATE_ABBRS) + r")\b", re.I
)


def is_us_location(location: str) -> bool:
    """Heuristic: does this posting location denote somewhere in the US?

    Matches on: explicit country string, any US state name, any US state
    abbreviation (word-bounded), or a bare 'remote' (most watched boards are
    US companies, so US-remote is the common case — a deliberate tradeoff
    that favors recall; the user can dismiss stray non-US remote roles)."""
    if not location:
        return False
    loc = location.lower()
    if _US_COUNTRY_RE.search(loc):
        return True
    if _US_STATE_NAME_RE.search(loc):
        return True
    if _US_STATE_ABBR_RE.search(loc):
        return True
    return "remote" in loc


def location_matches(location: str, filter_terms: list[str]) -> bool:
    """True if the posting location satisfies any of the user's location
    filters. Country terms ("United States") use the US heuristic; everything
    else (cities, states) uses word-boundary substring matching for precision.
    Empty filter_terms means 'no constraint' — caller handles that."""
    if not filter_terms:
        return True
    location = location or ""
    for raw in filter_terms:
        term = raw.strip().lower()
        if not term:
            continue
        if term in _US_COUNTRY_TERMS:
            if is_us_location(location):
                return True
            continue
        # City / state precision: expand synonyms (e.g. remote→wfh) and
        # word-boundary match.
        for expanded in expand_synonyms([term]):
            if _term_regex(expanded).search(location):
                return True
    return False


def expand_synonyms(terms: list[str]) -> set[str]:
    """Expand each term to its synonym group. Terms with no group pass through."""
    expanded: set[str] = set()
    for term in terms:
        t = term.strip().lower()
        if not t:
            continue
        if t in _SYNONYM_INDEX:
            expanded.update(_SYNONYM_INDEX[t])
        else:
            expanded.add(t)
    return expanded


def _term_regex(term: str) -> re.Pattern:
    """Word-boundary regex for a term. Handles multi-word phrases by allowing
    any whitespace between tokens ('machine learning' matches 'machine   learning')."""
    parts = [re.escape(p) for p in term.split()]
    # Anchor with \b on outer edges; \s+ between tokens.
    inner = r"\s+".join(parts)
    return re.compile(rf"(?<!\w){inner}(?!\w)", re.I)


def contains_any(text: str, terms: set[str]) -> bool:
    """True if any term matches text at word boundaries."""
    if not terms:
        return False
    return any(_term_regex(term).search(text) for term in terms)


def infer_job_types(title: str) -> set[str]:
    """Extract job type tags from a posting title. Returns canonical keys
    matching what a user can filter on: 'internship', 'new_grad', etc."""
    types: set[str] = set()
    for key, pattern in _JOB_TYPE_PATTERNS.items():
        if pattern.search(title):
            types.add(key)
    return types


def matches(
    *,
    title: str,
    location: str = "",
    description: str = "",
    keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    locations: list[str] | None = None,
    job_types: list[str] | None = None,
    search_description: bool = False,
) -> bool:
    """Decide whether a posting matches a rule.

    All filters are ANDed: keyword match AND location match AND job-type match
    AND no excludes hit. Empty filters mean 'no constraint' (i.e., match-all).
    """
    keywords = keywords or []
    exclude_keywords = exclude_keywords or []
    locations = locations or []
    job_types = job_types or []

    title = title or ""
    location = location or ""
    haystack = title
    if search_description and description:
        haystack = f"{title}\n{description}"

    # Exclusions win — check first, short-circuit.
    if exclude_keywords:
        excludes = expand_synonyms(exclude_keywords)
        if contains_any(haystack, excludes):
            return False

    # Keywords: any keyword (after synonym expansion) must appear.
    if keywords:
        positives = expand_synonyms(keywords)
        if not contains_any(haystack, positives):
            return False

    # Locations: country-aware (see location_matches). Country terms like
    # "United States" match via US state/abbr heuristic; cities/states use
    # word-boundary precision.
    if locations and not location_matches(location, locations):
        return False

    # Job types: title must resolve to at least one of the requested types.
    if job_types:
        # Normalize user-supplied types (allow "internship" or "intern" etc.)
        requested = set()
        for jt in job_types:
            jt_norm = jt.strip().lower().replace("-", "_").replace(" ", "_")
            requested.add(jt_norm)
        inferred = infer_job_types(title)
        if not (requested & inferred):
            return False

    return True
