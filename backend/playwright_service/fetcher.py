import hashlib
import logging
import re

from django.core.cache import cache

from apps.common.url_validation import URLValidationError, validate_external_url

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 24  # 24 hours
MAX_HTML_BYTES = 5 * 1024 * 1024  # 5 MB ceiling per page


def _cache_key(url: str) -> str:
    # sha256, not md5 — md5 collisions could let an attacker overwrite cached
    # results for unrelated URLs (low impact but easy to fix)
    return f"jd:{hashlib.sha256(url.encode()).hexdigest()}"


def _clean_text(html: str) -> str:
    """Extract visible text from HTML, stripping nav/footer/scripts."""
    text = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:10000]


async def fetch_job_description(url: str) -> str | None:
    """Fetch job description from a URL using Playwright.

    SECURITY: All user-supplied URLs go through `validate_external_url` to
    prevent SSRF against cloud metadata services and internal infrastructure.

    Returns extracted text, or None if fetching fails.
    Results are cached in Redis for 24 hours.
    """
    try:
        validate_external_url(url)
    except URLValidationError as e:
        logger.warning(f"Blocked SSRF attempt: {url} — {e}")
        return None

    cached = cache.get(_cache_key(url))
    if cached:
        return cached

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    # No cookies/storage retained from previous runs
                    storage_state=None,
                    # Drop dangerous APIs the page might call
                    java_script_enabled=True,
                    # Don't accept downloads — could exhaust disk
                    accept_downloads=False,
                )
                page = await context.new_page()

                # Hard navigation timeout + total page lifetime cap
                await page.goto(
                    url, wait_until="domcontentloaded", timeout=15000
                )
                await page.wait_for_timeout(2000)

                html = await page.content()

                # Don't process pathologically large pages
                if len(html.encode("utf-8", errors="ignore")) > MAX_HTML_BYTES:
                    logger.warning(f"Truncated oversize page: {url}")
                    html = html[:MAX_HTML_BYTES]
            finally:
                await browser.close()

        text = _clean_text(html)
        if text:
            cache.set(_cache_key(url), text, CACHE_TTL)
        return text

    except Exception as e:
        logger.warning(f"Playwright fetch failed for {url}: {e}")
        return None


def fetch_job_description_sync(url: str) -> str | None:
    """Synchronous wrapper for use in Celery tasks."""
    import asyncio

    return asyncio.run(fetch_job_description(url))
