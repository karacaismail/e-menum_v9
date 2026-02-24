"""
Bot verification system for SEO Shield.

Verifies the identity of search engine bots and social media crawlers
using DNS reverse lookup, IP range matching, and User-Agent analysis.

Supported verification methods:
- DNS: Reverse DNS lookup + forward DNS confirmation (Googlebot, Bingbot, etc.)
- IP Range: CIDR block matching for bots with known IP ranges
- User-Agent: Pattern matching only (social media crawlers)

Usage:
    verifier = BotVerifier()
    is_verified, bot_name = verifier.verify_bot('66.249.66.1', 'Googlebot/2.1')
"""

import ipaddress
import logging
import re
import socket
from typing import Optional

from django.core.cache import cache

logger = logging.getLogger('apps.seo_shield')

# Cache key prefix for bot whitelist entries
CACHE_KEY_BOT_WHITELIST = 'shield:bot_whitelist'
CACHE_TTL_BOT_WHITELIST = 300  # 5 minutes

# Cache key prefix for DNS verification results
CACHE_KEY_DNS_RESULT = 'shield:dns_verify:{ip}'
CACHE_TTL_DNS_RESULT = 3600  # 1 hour

# Default bot definitions used as fallback when the database is empty.
# These cover major search engines and social media crawlers.
DEFAULT_BOTS = {
    'Googlebot': {
        'pattern': r'Googlebot',
        'dns_domain': 'googlebot.com',
        'method': 'dns',
        'ip_ranges': [],
    },
    'Bingbot': {
        'pattern': r'bingbot',
        'dns_domain': 'search.msn.com',
        'method': 'dns',
        'ip_ranges': [],
    },
    'DuckDuckBot': {
        'pattern': r'DuckDuckBot',
        'dns_domain': 'duckduckgo.com',
        'method': 'dns',
        'ip_ranges': [],
    },
    'YandexBot': {
        'pattern': r'YandexBot',
        'dns_domain': 'yandex.ru',
        'method': 'dns',
        'ip_ranges': [],
    },
    'Baiduspider': {
        'pattern': r'Baiduspider',
        'dns_domain': 'baidu.com',
        'method': 'dns',
        'ip_ranges': [],
    },
    'facebookexternalhit': {
        'pattern': r'facebookexternalhit',
        'dns_domain': '',
        'method': 'user_agent',
        'ip_ranges': [],
    },
    'Twitterbot': {
        'pattern': r'Twitterbot',
        'dns_domain': '',
        'method': 'user_agent',
        'ip_ranges': [],
    },
    'LinkedInBot': {
        'pattern': r'LinkedInBot',
        'dns_domain': '',
        'method': 'user_agent',
        'ip_ranges': [],
    },
}


class BotVerifier:
    """
    Verifies the identity of bots claiming to be legitimate crawlers.

    Loads active BotWhitelist entries from the database (with caching)
    and falls back to DEFAULT_BOTS when no entries are found.

    Verification flow:
    1. Check User-Agent against known bot patterns
    2. If a match is found, verify identity using the configured method:
       - dns: Reverse DNS lookup + forward DNS confirmation
       - ip_range: Check IP against known CIDR blocks
       - user_agent: Accept based on User-Agent match alone
    """

    def __init__(self):
        """Initialize the BotVerifier. Bot list is loaded lazily on first use."""
        self._bot_list = None

    def verify_bot(self, ip_address: str, user_agent: str) -> tuple[bool, Optional[str]]:
        """
        Verify whether a request comes from a legitimate bot.

        Args:
            ip_address: The client IP address to verify.
            user_agent: The User-Agent header string.

        Returns:
            A tuple of (is_verified, bot_name).
            - is_verified: True if the bot identity is confirmed.
            - bot_name: Name of the matched bot, or None if no match.
        """
        if not user_agent:
            return False, None

        bot_list = self._get_bot_whitelist()

        for bot_entry in bot_list:
            name = bot_entry['name']
            pattern = bot_entry['pattern']
            method = bot_entry['method']
            dns_domain = bot_entry.get('dns_domain', '')
            ip_ranges = bot_entry.get('ip_ranges', [])

            # Check if User-Agent matches this bot's pattern
            if not self._ua_match(user_agent, pattern):
                continue

            # User-Agent matched. Now verify using the configured method.
            if method == 'dns' and dns_domain:
                is_verified = self._dns_verify(ip_address, dns_domain)
                if is_verified:
                    logger.info(
                        "Bot verified via DNS: %s from %s",
                        name, ip_address,
                    )
                    return True, name
                else:
                    logger.warning(
                        "Bot DNS verification failed: UA claims %s but IP %s "
                        "does not resolve to %s",
                        name, ip_address, dns_domain,
                    )
                    return False, name

            elif method == 'ip_range' and ip_ranges:
                is_verified = self._ip_range_verify(ip_address, ip_ranges)
                if is_verified:
                    logger.info(
                        "Bot verified via IP range: %s from %s",
                        name, ip_address,
                    )
                    return True, name
                else:
                    logger.warning(
                        "Bot IP range verification failed: UA claims %s but "
                        "IP %s is not in known ranges",
                        name, ip_address,
                    )
                    return False, name

            elif method == 'user_agent':
                # User-Agent only verification: accept if UA matches.
                # This is used for social media bots that don't have
                # reliable DNS or IP range verification.
                logger.debug(
                    "Bot accepted via UA match only: %s from %s",
                    name, ip_address,
                )
                return True, name

            else:
                # Unknown method or missing config, treat as unverified match
                logger.warning(
                    "Bot matched but verification method '%s' is not "
                    "supported or misconfigured for %s",
                    method, name,
                )
                return False, name

        # No bot pattern matched
        return False, None

    def _dns_verify(self, ip_address: str, expected_domain: str) -> bool:
        """
        Verify a bot's identity via reverse DNS lookup.

        Performs a two-step verification:
        1. Reverse DNS: IP -> hostname (must end with expected_domain)
        2. Forward DNS: hostname -> IP (must match original IP)

        Args:
            ip_address: The IP address to verify.
            expected_domain: The expected domain suffix (e.g., 'googlebot.com').

        Returns:
            True if the IP verifies as belonging to the expected domain.
        """
        # Check cache first
        cache_key = CACHE_KEY_DNS_RESULT.format(ip=ip_address)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result.get('domain', '') == expected_domain and cached_result.get('verified', False)

        try:
            # Step 1: Reverse DNS lookup (IP -> hostname)
            hostname, _, _ = socket.gethostbyaddr(ip_address)

            # Check if hostname ends with the expected domain
            if not hostname.endswith('.' + expected_domain) and not hostname.endswith('.' + expected_domain + '.'):
                # Also check if hostname IS the domain (unlikely but possible)
                if hostname != expected_domain:
                    cache.set(cache_key, {'domain': '', 'verified': False}, CACHE_TTL_DNS_RESULT)
                    return False

            # Step 2: Forward DNS lookup (hostname -> IP)
            resolved_ips = socket.gethostbyname_ex(hostname)[2]

            verified = ip_address in resolved_ips
            cache.set(
                cache_key,
                {'domain': expected_domain if verified else '', 'verified': verified},
                CACHE_TTL_DNS_RESULT,
            )
            return verified

        except (socket.herror, socket.gaierror, socket.timeout, OSError) as exc:
            logger.debug(
                "DNS verification failed for %s (expected %s): %s",
                ip_address, expected_domain, exc,
            )
            cache.set(cache_key, {'domain': '', 'verified': False}, CACHE_TTL_DNS_RESULT)
            return False

    def _ip_range_verify(self, ip_address: str, ip_ranges: list[str]) -> bool:
        """
        Check if an IP address falls within any of the given CIDR ranges.

        Args:
            ip_address: The IP address to check.
            ip_ranges: List of CIDR notation strings (e.g., ['66.249.64.0/19']).

        Returns:
            True if the IP is within any of the provided ranges.
        """
        try:
            addr = ipaddress.ip_address(ip_address)
        except ValueError:
            logger.warning("Invalid IP address for range check: %s", ip_address)
            return False

        for cidr in ip_ranges:
            try:
                network = ipaddress.ip_network(cidr, strict=False)
                if addr in network:
                    return True
            except ValueError:
                logger.warning("Invalid CIDR range in bot config: %s", cidr)
                continue

        return False

    def _ua_match(self, user_agent: str, pattern: str) -> bool:
        """
        Check if a User-Agent string matches a regex pattern.

        Args:
            user_agent: The full User-Agent header string.
            pattern: Regex pattern to search for in the User-Agent.

        Returns:
            True if the pattern is found in the User-Agent string.
        """
        try:
            return bool(re.search(pattern, user_agent, re.IGNORECASE))
        except re.error:
            logger.warning("Invalid regex pattern in bot config: %s", pattern)
            return False

    def _get_bot_whitelist(self) -> list[dict]:
        """
        Return the list of bot entries to check against.

        Loads active BotWhitelist entries from the database with a 5-minute
        cache TTL. Falls back to DEFAULT_BOTS if no active entries exist
        in the database.

        Returns:
            List of dicts with keys: name, pattern, method, dns_domain, ip_ranges.
        """
        if self._bot_list is not None:
            return self._bot_list

        # Try cache first
        cached = cache.get(CACHE_KEY_BOT_WHITELIST)
        if cached is not None:
            self._bot_list = cached
            return cached

        # Load from database
        try:
            from apps.seo_shield.models import BotWhitelist

            db_entries = BotWhitelist.objects.filter(is_active=True).values(
                'name',
                'user_agent_pattern',
                'verification_method',
                'dns_domain',
                'ip_ranges',
            )

            bot_list = []
            for entry in db_entries:
                bot_list.append({
                    'name': entry['name'],
                    'pattern': entry['user_agent_pattern'],
                    'method': entry['verification_method'],
                    'dns_domain': entry['dns_domain'] or '',
                    'ip_ranges': entry['ip_ranges'] or [],
                })

            if bot_list:
                cache.set(CACHE_KEY_BOT_WHITELIST, bot_list, CACHE_TTL_BOT_WHITELIST)
                self._bot_list = bot_list
                return bot_list

        except Exception as exc:
            logger.warning(
                "Failed to load BotWhitelist from database, "
                "falling back to defaults: %s",
                exc,
            )

        # Fallback to defaults
        default_list = []
        for name, config in DEFAULT_BOTS.items():
            default_list.append({
                'name': name,
                'pattern': config['pattern'],
                'method': config['method'],
                'dns_domain': config['dns_domain'],
                'ip_ranges': config.get('ip_ranges', []),
            })

        cache.set(CACHE_KEY_BOT_WHITELIST, default_list, CACHE_TTL_BOT_WHITELIST)
        self._bot_list = default_list
        return default_list

    def invalidate_cache(self):
        """
        Invalidate the cached bot whitelist.

        Call this when BotWhitelist entries are modified in the admin
        to force a reload on the next request.
        """
        cache.delete(CACHE_KEY_BOT_WHITELIST)
        self._bot_list = None
