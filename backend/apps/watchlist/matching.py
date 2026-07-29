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
    for term in terms:
        if _term_regex(term).search(text):
            return True
    return False


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

    # Locations: any listed location must appear in the posting's location field.
    if locations:
        loc_terms = expand_synonyms(locations)
        if not contains_any(location, loc_terms):
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
