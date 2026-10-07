"""Web page content extraction service.

Uses trafilatura to extract article content from web pages with zero headless
browser dependency. Falls back to a lightweight HTML parser when trafilatura
is not available or extraction fails.
"""
import re
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(
    r'https?://[^\s<>\"\']+[a-zA-Z0-9/]'
)


def is_url(text: str) -> bool:
    """Check if text is a URL."""
    return bool(_URL_PATTERN.match(text.strip()))


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    return _URL_PATTERN.findall(text)


async def fetch_page(url: str) -> Optional[Dict[str, Any]]:
    """Fetch and extract content from a web page.

    Returns dict with keys:
        title: str
        content: str
        html: str  (raw HTML, for fallback processing)
        images: list of absolute image URLs
        author: Optional[str]
        description: Optional[str]
    """
    try:
        import httpx
        resp = await httpx.AsyncClient(timeout=15.0).get(url)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None

    try:
        result = await _extract_with_trafilatura(html, url)
    except Exception:
        result = await _extract_with_fallback(html, url)

    return result


async def _extract_with_trafilatura(html: str, url: str) -> Optional[Dict[str, Any]]:
    """Primary extraction using trafilatura (if installed)."""
    import trafilatura
    extracted = trafilatura.extract(
        html,
        include_comments=False,
        include_links=False,
        include_tables=True,
        include_images=True,
    )
    if not extracted or len(extracted.strip()) < 50:
        return None

    title = trafilatura.extract_metadata(html).get("title", "")
    description = trafilatura.extract_metadata(html).get("description", "")
    author = trafilatura.extract_metadata(html).get("author", "")

    images = _extract_image_urls(html, url)

    return {
        "title": title or url.split("/")[2],
        "content": extracted.strip(),
        "html": html,
        "images": images,
        "author": author or None,
        "description": description or None,
    }


async def _extract_with_fallback(html: str, url: str) -> Dict[str, Any]:
    """Lightweight fallback extraction using regex (no extra dependencies)."""
    import re

    # Extract title
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else ""

    # Extract meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if not desc_match:
        desc_match = re.search(
            r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']',
            html, re.IGNORECASE
        )
    description = desc_match.group(1).strip() if desc_match else ""

    # Strip tags to get plain text content
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'&\w+;', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Prefer article/main content region
    main_match = re.search(
        r'<article[^>]*>(.*?)</article>', clean, re.DOTALL | re.IGNORECASE
    )
    if not main_match:
        main_match = re.search(
            r'<main[^>]*>(.*?)</main>', clean, re.DOTALL | re.IGNORECASE
        )
    content = main_match.group(1).strip() if main_match else clean[:2000]

    images = _extract_image_urls(html, url)

    return {
        "title": title or url.split("/")[2],
        "content": content,
        "html": html,
        "images": images,
        "author": None,
        "description": description or None,
    }


def _extract_image_urls(html: str, base_url: str) -> List[str]:
    """Extract image URLs from HTML, converting relative paths to absolute."""
    from urllib.parse import urljoin
    src_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    alt_matches = re.findall(r'<img[^>]+alt=["\']([^"\']+)["\']', html)
    urls = []
    for src in src_matches:
        abs_url = urljoin(base_url, src)
        if abs_url.startswith("data:") or abs_url.startswith("about:blank"):
            continue
        urls.append(abs_url)
    return urls


# Public async interface
async def fetch_web_content(url: str) -> Optional[Dict[str, Any]]:
    """Convenience wrapper for fetching and extracting web page content."""
    import asyncio
    try:
        return await asyncio.wait_for(fetch_page(url), timeout=20.0)
    except Exception as e:
        logger.error(f"Web fetch failed for {url}: {e}")
        return None
