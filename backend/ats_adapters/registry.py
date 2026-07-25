import re

import httpx

from .ashby import AshbyAdapter
from .base import ATSAdapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .smartrecruiters import SmartRecruitersAdapter
from .workable import WorkableAdapter

ADAPTERS: list[ATSAdapter] = [
    GreenhouseAdapter(),
    LeverAdapter(),
    AshbyAdapter(),
    WorkableAdapter(),
    SmartRecruitersAdapter(),
]

ATS_SIGNATURES = {
    "greenhouse": [
        r"boards\.greenhouse\.io",
        r"greenhouse\.io/embed",
        r'id="grnhse_app"',
    ],
    "lever": [
        r"jobs\.lever\.co",
        r"lever\.co",
    ],
    "ashby": [
        r"jobs\.ashbyhq\.com",
    ],
    "workable": [
        r"apply\.workable\.com",
    ],
    "smartrecruiters": [
        r"smartrecruiters\.com",
    ],
}


def get_adapter(ats_provider: str) -> ATSAdapter | None:
    for adapter in ADAPTERS:
        if adapter.name == ats_provider:
            return adapter
    return None


def detect_ats_from_url(url: str) -> tuple[str, str] | None:
    """Detect ATS provider and extract company slug from a URL.

    Returns (provider_name, company_slug) or None.
    """
    for adapter in ADAPTERS:
        if adapter.detect(url):
            slug = adapter.extract_company_identifier(url)
            if slug:
                return adapter.name, slug
    return None


async def detect_ats_from_page(url: str) -> tuple[str, str] | None:
    """Fetch a careers page and detect ATS from HTML content.

    SECURITY: URL validation prevents SSRF. Note that follow_redirects=True
    means we also need to validate the *final* URL after redirects, since an
    attacker could host a redirector at a public URL pointing to internal IPs.
    """
    from apps.common.url_validation import URLValidationError, validate_external_url

    result = detect_ats_from_url(url)
    if result:
        return result

    try:
        validate_external_url(url)
    except URLValidationError:
        return None

    try:
        # follow_redirects=False so we can validate each hop ourselves
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=False,
            limits=httpx.Limits(max_keepalive_connections=1, max_connections=2),
        ) as client:
            response = await client.get(url)

            # Manually follow up to 5 redirects, validating each
            redirect_count = 0
            while response.is_redirect and redirect_count < 5:
                next_url = response.headers.get("Location", "")
                if not next_url:
                    break
                if next_url.startswith("/"):
                    # relative — safe, same host
                    from urllib.parse import urljoin
                    next_url = urljoin(str(response.url), next_url)
                try:
                    validate_external_url(next_url)
                except URLValidationError:
                    return None
                response = await client.get(next_url)
                redirect_count += 1

            # Cap response size at 5 MB to prevent memory exhaustion
            html = response.text[: 5 * 1024 * 1024]
            final_url = str(response.url)

        result = detect_ats_from_url(final_url)
        if result:
            return result

        for provider, patterns in ATS_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    adapter = get_adapter(provider)
                    if adapter:
                        slug = adapter.extract_company_identifier(final_url)
                        if not slug:
                            match = re.search(pattern, html, re.IGNORECASE)
                            if match:
                                slug = adapter.extract_company_identifier(
                                    match.group(0)
                                )
                        if slug:
                            return provider, slug

    except (httpx.HTTPError, Exception):
        pass

    return None
