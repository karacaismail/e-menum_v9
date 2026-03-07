"""
Broken link checker for the E-Menum marketing site.

Provides a ``BrokenLinkChecker`` class that can:
    1. Check individual URLs (HEAD with GET fallback)
    2. Crawl a single page and check all its ``<a href>`` links
    3. Perform a full site crawl following internal links
    4. Save broken-link results to the ``BrokenLink`` model

Uses the ``requests`` library when available; degrades gracefully
if it is not installed (all checks return status ``0``).
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("apps.seo")

# ──────────────────────────────────────────────────────────────────────────────
# Optional ``requests`` import
# ──────────────────────────────────────────────────────────────────────────────

try:
    import requests as _requests  # noqa: F401 (used throughout)

    HAS_REQUESTS = True
except ImportError:
    _requests = None  # type: ignore[assignment]
    HAS_REQUESTS = False
    logger.warning(
        'The "requests" library is not installed. '
        "BrokenLinkChecker will return status 0 for all checks."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Regex for extracting <a href="..."> from HTML
# ──────────────────────────────────────────────────────────────────────────────

_HREF_RE = re.compile(
    r'<a\s[^>]*href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# User-Agent string for requests
_USER_AGENT = f"E-Menum-LinkChecker/1.0 (+https://{settings.SITE_DOMAIN})"


# ──────────────────────────────────────────────────────────────────────────────
# BrokenLinkChecker
# ──────────────────────────────────────────────────────────────────────────────


class BrokenLinkChecker:
    """
    Crawls pages and checks links for broken (4xx/5xx) responses.

    Parameters
    ----------
    base_url:
        The root URL of the site (e.g. ``https://e-menum.net``).
        If ``None``, it must be supplied later to :meth:`full_site_crawl`.
    timeout:
        Timeout in seconds for each HTTP request.  Defaults to ``10``.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.timeout = timeout

    # ── Single URL check ─────────────────────────────────────────────────

    def check_url(self, url: str) -> int:
        """
        Check a single URL.

        Attempts a ``HEAD`` request first (cheaper); falls back to ``GET``
        if the server returns 405 Method Not Allowed.

        Returns
        -------
        int
            HTTP status code, or ``0`` on connection/timeout error.
        """
        if not HAS_REQUESTS:
            return 0

        headers = {"User-Agent": _USER_AGENT}

        try:
            resp = _requests.head(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            # Some servers reject HEAD; retry with GET
            if resp.status_code == 405:
                resp = _requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                    stream=True,  # Don't download the entire body
                )
                resp.close()
            return resp.status_code

        except _requests.exceptions.Timeout:
            logger.debug("Timeout checking URL: %s", url)
            return 0
        except _requests.exceptions.ConnectionError:
            logger.debug("Connection error checking URL: %s", url)
            return 0
        except _requests.exceptions.RequestException as exc:
            logger.debug("Request error checking URL %s: %s", url, exc)
            return 0

    # ── Single page crawl ────────────────────────────────────────────────

    def crawl_page(self, url: str) -> List[Tuple[str, int]]:
        """
        Fetch *url*, extract all ``<a href>`` links, and check each one.

        Parameters
        ----------
        url:
            The page URL to crawl.

        Returns
        -------
        list of (link_url, status_code) tuples
            One entry per link found on the page.
        """
        if not HAS_REQUESTS:
            return []

        headers = {"User-Agent": _USER_AGENT}
        results: List[Tuple[str, int]] = []

        try:
            resp = _requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
        except _requests.exceptions.RequestException as exc:
            logger.warning("Failed to fetch page %s: %s", url, exc)
            return results

        if resp.status_code != 200:
            logger.debug("Page %s returned status %d", url, resp.status_code)
            return results

        # Extract hrefs
        hrefs = _HREF_RE.findall(resp.text)
        seen: Set[str] = set()

        for href in hrefs:
            # Skip anchors, javascript, mailto, tel
            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            # Resolve relative URLs
            absolute = urljoin(url, href)

            # Deduplicate
            if absolute in seen:
                continue
            seen.add(absolute)

            status = self.check_url(absolute)
            results.append((absolute, status))

        return results

    # ── Full site crawl ──────────────────────────────────────────────────

    def full_site_crawl(
        self,
        start_url: Optional[str] = None,
        max_pages: int = 100,
    ) -> Dict[str, List[Tuple[str, int]]]:
        """
        Crawl the site starting from *start_url*, following internal links.

        Only pages on the same domain as :attr:`base_url` are crawled.
        External links are checked but not followed.

        Parameters
        ----------
        start_url:
            URL to start crawling from.  Defaults to :attr:`base_url`.
        max_pages:
            Maximum number of pages to crawl (avoids infinite loops).
            Defaults to ``100``.

        Returns
        -------
        dict
            ``{page_url: [(link_url, status_code), ...]}``
        """
        if not HAS_REQUESTS:
            logger.error(
                'Cannot run full site crawl: "requests" library not installed.'
            )
            return {}

        start = start_url or self.base_url
        if not start:
            logger.error("No start URL or base_url configured for site crawl.")
            return {}

        base_parsed = urlparse(start)
        base_domain = base_parsed.netloc

        visited: Set[str] = set()
        queue: List[str] = [start]
        all_results: Dict[str, List[Tuple[str, int]]] = {}

        while queue and len(visited) < max_pages:
            current_url = queue.pop(0)

            # Normalise (strip fragment)
            current_parsed = urlparse(current_url)
            current_clean = current_parsed._replace(fragment="").geturl()

            if current_clean in visited:
                continue
            visited.add(current_clean)

            logger.info(
                "Crawling page %d/%d: %s", len(visited), max_pages, current_clean
            )

            page_results = self.crawl_page(current_clean)
            all_results[current_clean] = page_results

            # Enqueue internal links that returned 200
            for link_url, status in page_results:
                link_parsed = urlparse(link_url)
                link_clean = link_parsed._replace(fragment="").geturl()

                # Only follow internal pages
                if link_parsed.netloc == base_domain and link_clean not in visited:
                    # Skip non-page resources
                    if not _looks_like_page(link_parsed.path):
                        continue
                    queue.append(link_clean)

        logger.info("Site crawl complete: %d pages crawled.", len(visited))
        return all_results

    # ── Persist results ──────────────────────────────────────────────────

    def save_results(
        self,
        results: Dict[str, List[Tuple[str, int]]],
    ) -> int:
        """
        Save broken links (status >= 400 or 0) to the ``BrokenLink`` model.

        Existing records matching ``(source_url, target_url)`` are updated
        (status, last_checked, check_count incremented).  New records are
        created for previously unseen broken links.

        Fires the ``broken_link_found`` signal for each new broken link.

        Returns the total number of broken-link records upserted.
        """
        from apps.core.events import broken_link_found
        from apps.seo.models import BrokenLink

        saved = 0
        now = timezone.now()

        for source_url, links in results.items():
            for target_url, status_code in links:
                # Only persist broken links
                if status_code == 0 or status_code >= 400:
                    existing = BrokenLink.objects.filter(
                        source_url=source_url,
                        target_url=target_url,
                    ).first()

                    if existing:
                        existing.status_code = status_code
                        existing.last_checked = now
                        existing.check_count += 1
                        # If previously resolved but broken again, mark unresolved
                        if existing.is_resolved:
                            existing.is_resolved = False
                            existing.resolved_at = None
                        existing.save(
                            update_fields=[
                                "status_code",
                                "last_checked",
                                "check_count",
                                "is_resolved",
                                "resolved_at",
                            ]
                        )
                    else:
                        BrokenLink.objects.create(
                            source_url=source_url,
                            target_url=target_url,
                            status_code=status_code,
                            source_page=urlparse(source_url).path,
                        )
                        # Fire event for new broken links
                        broken_link_found.send(
                            sender=self.__class__,
                            source_url=source_url,
                            target_url=target_url,
                            status_code=status_code,
                        )
                    saved += 1

        logger.info("Saved %d broken link records.", saved)
        return saved


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _looks_like_page(path: str) -> bool:
    """
    Return ``True`` if *path* looks like an HTML page rather than a
    static asset.

    Filters out common static-file extensions so the crawler doesn't
    waste time on images, CSS, JS, etc.
    """
    skip_extensions = {
        ".css",
        ".js",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".map",
        ".pdf",
        ".zip",
        ".gz",
        ".mp4",
        ".webm",
        ".mp3",
        ".wav",
    }
    # Extract extension from the last path segment
    last_segment = path.rsplit("/", 1)[-1]
    if "." in last_segment:
        ext = "." + last_segment.rsplit(".", 1)[-1].lower()
        if ext in skip_extensions:
            return False
    return True
