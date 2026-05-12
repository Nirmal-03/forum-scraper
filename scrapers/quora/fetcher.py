"""Quora HTTP fetch logic — uses curl_cffi to bypass Cloudflare.

Quora is behind Cloudflare and requires TLS fingerprint impersonation.
Uses a session-based approach to maintain cookies across requests.
"""

import re
import time

from curl_cffi import requests as cffi_requests

from core.config import settings
from core.exceptions import FetchTimeoutError, MaxRetriesError, ParseError

GRAPHQL_ENDPOINT = "https://www.quora.com/graphql/gql_para_POST"


class QuoraFetcher:
    """Handles all HTTP communication with Quora.

    Uses curl_cffi with Chrome TLS fingerprint to bypass Cloudflare.
    Maintains a session for cookie persistence across requests.
    """

    def __init__(self):
        self._session = cffi_requests.Session(impersonate="chrome120")
        self._formkey: str | None = None
        self._revision: str | None = None
        self._feed_hash: str | None = None
        self._tid: int | None = None

    def initialize(self, topic_url: str) -> None:
        """Fetch the topic page and extract auth tokens + feed hash.

        Must be called before fetch_feed_page().

        Args:
            topic_url: Normalized Quora topic URL.

        Raises:
            MaxRetriesError: If the topic page cannot be fetched.
            ParseError: If required tokens cannot be extracted.
        """
        html = self._fetch_page(topic_url)

        # Extract formkey and revision from page data
        formkey_match = re.search(r'"formkey"\s*:\s*"([^"]+)"', html)
        revision_match = re.search(r'"revision"\s*:\s*"([^"]+)"', html)

        if not formkey_match or not revision_match:
            raise ParseError("Failed to extract Quora auth tokens (formkey/revision)")

        self._formkey = formkey_match.group(1)
        self._revision = revision_match.group(1)

        # Extract topic ID (tid)
        tid_match = re.search(r'"tid"\s*:\s*(\d+)', html)
        if not tid_match:
            raise ParseError("Failed to extract topic ID (tid) from page")
        self._tid = int(tid_match.group(1))

        # Find TopicTab-ReadWrite bundle URL and extract feed hash
        self._feed_hash = self._extract_feed_hash(html)

    def fetch_feed_page(self, cursor: str | None = None, page_num: int = 0) -> dict:
        """Fetch a page of the topic feed via GraphQL.

        Args:
            cursor: Pagination cursor (endCursor from previous page). None for first page.
            page_num: Zero-based page number (for multifeedNumBundlesOnClient).

        Returns:
            Raw JSON dict from the GraphQL response.

        Raises:
            MaxRetriesError: If the request fails after retries.
        """
        variables = {
            "tid": self._tid,
            "initialTab": "read",
            "multifeedNumBundlesOnClient": page_num * 10,
            "multifeedAfter": cursor,
            "first": 10,
        }

        payload = {
            "queryName": "TopicTabReadQuery",
            "variables": variables,
            "extensions": {"hash": self._feed_hash},
        }

        headers = {
            "content-type": "application/json",
            "quora-formkey": self._formkey,
            "quora-revision": self._revision,
        }

        for attempt in range(1, settings.QUORA_MAX_RETRIES + 1):
            try:
                response = self._session.post(
                    GRAPHQL_ENDPOINT,
                    json=payload,
                    headers=headers,
                    timeout=settings.QUORA_REQUEST_TIMEOUT,
                )

                if response.status_code == 200:
                    return response.json()

                if response.status_code in (429, 403):
                    time.sleep(attempt * 3)
                    continue

            except Exception as e:
                if attempt == settings.QUORA_MAX_RETRIES:
                    raise MaxRetriesError(
                        f"Failed to fetch Quora feed after {settings.QUORA_MAX_RETRIES} attempts: {e}"
                    )
                time.sleep(attempt * 2)

        raise MaxRetriesError(
            f"Failed to fetch Quora feed after {settings.QUORA_MAX_RETRIES} attempts"
        )

    def _fetch_page(self, url: str) -> str:
        """Fetch a page with retry logic.

        Returns:
            Response text.
        """
        for attempt in range(1, settings.QUORA_MAX_RETRIES + 1):
            try:
                response = self._session.get(url, timeout=settings.QUORA_REQUEST_TIMEOUT)

                if response.status_code == 200:
                    return response.text

                if response.status_code in (429, 403):
                    time.sleep(attempt * 3)
                    continue

            except Exception as e:
                if attempt == settings.QUORA_MAX_RETRIES:
                    raise MaxRetriesError(
                        f"Failed to fetch {url} after {settings.QUORA_MAX_RETRIES} attempts: {e}"
                    )
                time.sleep(attempt * 2)

        raise MaxRetriesError(f"Failed to fetch {url} after {settings.QUORA_MAX_RETRIES} attempts")

    def _extract_feed_hash(self, page_html: str) -> str:
        """Extract the GraphQL feed hash from the TopicTab-ReadWrite JS bundle.

        Args:
            page_html: HTML of the topic page.

        Returns:
            64-character hex hash string.

        Raises:
            ParseError: If the bundle or hash cannot be found.
        """
        # Find TopicTab-ReadWrite bundle URL
        js_urls = re.findall(r'(https://qsbr\.cf2\.quoracdn\.net/[^"\'>\s]+)', page_html)
        topic_tab_urls = [u for u in js_urls if "TopicTab-ReadWrite" in u]

        if not topic_tab_urls:
            raise ParseError("Could not find TopicTab-ReadWrite JS bundle URL")

        bundle_text = self._fetch_page(topic_tab_urls[0])

        # Extract 64-char hex hashes from the bundle
        hashes = re.findall(r'"([a-f0-9]{64})"', bundle_text)
        if len(hashes) < 2:
            raise ParseError("Could not find feed hash in TopicTab bundle")

        # The second hash is the one that returns the full feed with multifeedConnection
        return hashes[1]
