"""
IndexNow API integration for instant search engine URL notification.

IndexNow is a protocol that allows websites to notify search engines
(Bing, Yandex, Seznam, Naver) about URL changes in real time.

Usage:
    from apps.seo.indexnow import IndexNowClient

    client = IndexNowClient()
    client.submit_url("https://e-menum.net/blog/new-post/")
    client.submit_urls(["https://e-menum.net/page1/", "https://e-menum.net/page2/"])
"""

import logging
from typing import List, Optional

import requests
from django.conf import settings

logger = logging.getLogger("apps.seo")

# IndexNow API endpoint (Bing's endpoint also notifies other engines)
INDEXNOW_API_URL = "https://api.indexnow.org/indexnow"


class IndexNowClient:
    """
    Client for the IndexNow protocol.

    Submits URL change notifications to search engines via the IndexNow API.
    Requires an API key to be configured in settings or stored in TXTFileConfig.
    """

    def __init__(self, api_key: Optional[str] = None, host: Optional[str] = None):
        """
        Initialize the IndexNow client.

        Args:
            api_key: IndexNow API key. If not provided, reads from
                     settings.INDEXNOW_API_KEY or TXTFileConfig.
            host: Site hostname. If not provided, reads from
                  settings.SEO_CANONICAL_DOMAIN.
        """
        self.api_key = api_key or self._get_api_key()
        self.host = host or getattr(settings, "SEO_CANONICAL_DOMAIN", "")

    @staticmethod
    def _get_api_key() -> str:
        """
        Retrieve the IndexNow API key from settings or database.

        Priority:
        1. settings.INDEXNOW_API_KEY
        2. TXTFileConfig with file_type='indexnow'
        """
        key = getattr(settings, "INDEXNOW_API_KEY", "")
        if key:
            return key

        try:
            from apps.seo.models import TXTFileConfig

            config = TXTFileConfig.objects.filter(
                file_type="indexnow",
                is_active=True,
            ).first()
            if config:
                return config.content.strip()
        except Exception:
            pass

        return ""

    def submit_url(self, url: str) -> bool:
        """
        Submit a single URL to IndexNow.

        Args:
            url: The full URL to submit (must be on this site's domain).

        Returns:
            True if submission was successful, False otherwise.
        """
        if not self.api_key:
            logger.warning("IndexNow API key not configured; skipping submission")
            return False

        if not self.host:
            logger.warning("IndexNow host not configured; skipping submission")
            return False

        try:
            response = requests.get(
                INDEXNOW_API_URL,
                params={
                    "url": url,
                    "key": self.api_key,
                },
                timeout=10,
            )
            if response.status_code in (200, 202):
                logger.info(
                    "IndexNow: submitted %s (status=%d)", url, response.status_code
                )
                return True
            else:
                logger.warning(
                    "IndexNow: failed to submit %s (status=%d body=%s)",
                    url,
                    response.status_code,
                    response.text[:200],
                )
                return False
        except requests.RequestException as exc:
            logger.error("IndexNow: request failed for %s: %s", url, exc)
            return False

    def submit_urls(self, urls: List[str]) -> bool:
        """
        Submit multiple URLs to IndexNow in a single batch request.

        Args:
            urls: List of full URLs to submit.

        Returns:
            True if submission was successful, False otherwise.
        """
        if not self.api_key or not self.host:
            logger.warning("IndexNow not configured; skipping batch submission")
            return False

        if not urls:
            return True

        # IndexNow batch API supports up to 10,000 URLs
        try:
            payload = {
                "host": self.host,
                "key": self.api_key,
                "keyLocation": f"https://{self.host}/{self.api_key}.txt",
                "urlList": urls[:10000],
            }
            response = requests.post(
                INDEXNOW_API_URL,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=30,
            )
            if response.status_code in (200, 202):
                logger.info(
                    "IndexNow: batch submitted %d URLs (status=%d)",
                    len(urls),
                    response.status_code,
                )
                return True
            else:
                logger.warning(
                    "IndexNow: batch submission failed (status=%d body=%s)",
                    response.status_code,
                    response.text[:200],
                )
                return False
        except requests.RequestException as exc:
            logger.error("IndexNow: batch request failed: %s", exc)
            return False
