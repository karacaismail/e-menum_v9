"""
Multi-signal risk evaluation engine for SEO Shield.

Evaluates incoming requests against multiple risk signals and produces
a composite risk score with a recommended action. Each signal is scored
independently (0-100) and combined using weighted averaging.

Actions based on total score:
- pass      (< 30):   Allow request normally
- log       (30-60):  Allow but log for review
- challenge (60-80):  Consider challenging the client
- block     (> 80):   Block the request

Usage:
    engine = RiskEngine()
    result = engine.evaluate(request, ip_address='1.2.3.4', rate_limited=True)
    if result.action == 'block':
        return HttpResponse(status=429)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from django.conf import settings

logger = logging.getLogger("apps.seo_shield")


@dataclass
class RiskResult:
    """
    Result of a risk evaluation.

    Attributes:
        score: Composite risk score (0-100).
        signals: Dict mapping signal names to their individual scores.
        action: Recommended action ('pass', 'log', 'challenge', 'block').
    """

    score: int = 0
    signals: dict = field(default_factory=dict)
    action: str = "pass"


# Suspicious URL path patterns that indicate vulnerability scanners,
# misconfigurations, or malicious probing.
SUSPICIOUS_PATHS = [
    r"/\.env",
    r"/\.git",
    r"/\.svn",
    r"/\.htaccess",
    r"/\.htpasswd",
    r"/\.DS_Store",
    r"/wp-admin",
    r"/wp-login",
    r"/wp-content/uploads",
    r"/wp-includes",
    r"/xmlrpc\.php",
    r"/phpmyadmin",
    r"/phpMyAdmin",
    r"/pma",
    r"/adminer",
    r"/config\.(php|yml|yaml|json|ini|xml)",
    r"/backup",
    r"/dump",
    r"/database",
    r"/db\.(sql|sqlite|sqlite3)",
    r"/\.aws",
    r"/\.ssh",
    r"/etc/passwd",
    r"/etc/shadow",
    r"/proc/self",
    r"/actuator",
    r"/debug",
    r"/console",
    r"/server-status",
    r"/server-info",
    r"/cgi-bin",
    r"/shell",
    r"/cmd",
    r"/eval",
    r"/exec",
    r"/setup\.php",
    r"/install\.php",
    r"/admin\.php",
    r"/test\.php",
    r"/info\.php",
    r"/phpinfo",
]

# Known vulnerability scanner and attack tool User-Agent patterns.
SCANNER_USER_AGENTS = [
    r"sqlmap",
    r"nikto",
    r"nmap",
    r"masscan",
    r"zgrab",
    r"gobuster",
    r"dirbuster",
    r"wfuzz",
    r"ffuf",
    r"nuclei",
    r"httpx",
    r"burpsuite",
    r"burp\s?suite",
    r"owasp",
    r"acunetix",
    r"nessus",
    r"openvas",
    r"qualys",
    r"arachni",
    r"w3af",
    r"skipfish",
    r"havij",
    r"commix",
    r"whatweb",
    r"wpscan",
    r"joomscan",
    r"droopescan",
    r"cmsmap",
    r"curl/",  # curl without further identification
    r"wget/",  # wget without further identification
    r"python-requests",  # generic Python HTTP client
    r"python-urllib",
    r"go-http-client",
    r"java/",  # generic Java HTTP client
    r"libwww-perl",
    r"lwp-trivial",
    r"mechanize",
    r"scrapy",
    r"httpclient",
]

# Precompile regex patterns for performance
_SUSPICIOUS_PATH_RE = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATHS]
_SCANNER_UA_RE = [re.compile(p, re.IGNORECASE) for p in SCANNER_USER_AGENTS]


class RiskEngine:
    """
    Multi-signal risk evaluation engine.

    Evaluates each request against several risk signals and produces
    a composite score with a recommended action.
    """

    # Default score thresholds for actions (doubled for lower false-positive rate)
    THRESHOLD_LOG = 60
    THRESHOLD_CHALLENGE = 120
    THRESHOLD_BLOCK = 160

    # Signal weights (must match IPReputationManager.SIGNAL_WEIGHTS)
    SIGNAL_WEIGHTS = {
        "rate_limit": 0.30,
        "header_anomaly": 0.20,
        "path_pattern": 0.20,
        "ua_anomaly": 0.15,
        "robots_violation": 0.15,
    }

    def __init__(self):
        """
        Initialize the risk engine.

        Loads thresholds from Django settings if available, otherwise
        uses the class-level defaults.
        """
        self.threshold_log = getattr(
            settings,
            "SHIELD_THRESHOLD_LOG",
            self.THRESHOLD_LOG,
        )
        self.threshold_challenge = getattr(
            settings,
            "SHIELD_THRESHOLD_CHALLENGE",
            self.THRESHOLD_CHALLENGE,
        )
        self.threshold_block = getattr(
            settings,
            "SHIELD_THRESHOLD_BLOCK",
            self.THRESHOLD_BLOCK,
        )

    def evaluate(
        self,
        request,
        ip_address: str,
        rate_limited: bool = False,
        bot_verified: Optional[bool] = None,
    ) -> RiskResult:
        """
        Evaluate a request against all risk signals.

        Args:
            request: Django HttpRequest object.
            ip_address: Client IP address.
            rate_limited: Whether the client has exceeded rate limits.
            bot_verified: Result of bot verification.
                          True = verified bot, False = failed verification,
                          None = not a bot (UA didn't match any bot pattern).

        Returns:
            RiskResult with composite score, signal breakdown, and action.
        """
        signals = {}

        # Signal 1: Rate limiting
        signals["rate_limit"] = 100 if rate_limited else 0

        # Signal 2: Header anomaly detection
        signals["header_anomaly"] = self._check_header_anomaly(request)

        # Signal 3: Suspicious path pattern
        signals["path_pattern"] = self._check_path_pattern(request)

        # Signal 4: User-Agent anomaly
        signals["ua_anomaly"] = self._check_ua_anomaly(request, bot_verified)

        # Signal 5: Robots.txt violation
        # Not implemented in simple version; would require tracking
        # robots.txt rules and comparing against requested paths.
        signals["robots_violation"] = 0

        # Calculate weighted total
        total_score = self._calculate_weighted_score(signals)

        # Determine action
        action = self._determine_action(total_score)

        result = RiskResult(
            score=total_score,
            signals=signals,
            action=action,
        )

        if action != "pass":
            logger.debug(
                "Risk evaluation for %s: score=%d action=%s signals=%s",
                ip_address,
                total_score,
                action,
                signals,
            )

        return result

    def _check_header_anomaly(self, request) -> int:
        """
        Check for missing or suspicious HTTP headers.

        Legitimate browsers and well-behaved bots send standard headers
        like Accept, User-Agent, and Accept-Encoding. Missing or unusual
        values suggest automated tools or scraping.

        Args:
            request: Django HttpRequest object.

        Returns:
            Score between 0 (no anomaly) and 100 (highly suspicious).
        """
        score = 0

        user_agent = request.META.get("HTTP_USER_AGENT", "")
        accept = request.META.get("HTTP_ACCEPT", "")
        accept_encoding = request.META.get("HTTP_ACCEPT_ENCODING", "")
        accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")

        # No User-Agent header at all
        if not user_agent:
            score += 40

        # No Accept header
        if not accept:
            score += 25

        # No Accept-Encoding header (all modern browsers send this)
        if not accept_encoding:
            score += 15

        # No Accept-Language header (browsers always send this)
        if not accept_language:
            score += 10

        # Suspicious Accept-Encoding values
        if accept_encoding and accept_encoding.strip() == "*":
            score += 10

        return min(100, score)

    def _check_path_pattern(self, request) -> int:
        """
        Check if the requested path matches suspicious patterns.

        Scans for paths commonly targeted by vulnerability scanners
        and automated attack tools (e.g., /.env, /wp-admin, /phpmyadmin).

        Args:
            request: Django HttpRequest object.

        Returns:
            Score between 0 (normal path) and 100 (highly suspicious path).
        """
        path = request.path

        for pattern in _SUSPICIOUS_PATH_RE:
            if pattern.search(path):
                logger.debug(
                    "Suspicious path pattern matched: %s matched %s",
                    path,
                    pattern.pattern,
                )
                return 100

        # Check for common attack payloads in query string
        query_string = request.META.get("QUERY_STRING", "")
        if query_string:
            # SQL injection patterns
            sql_patterns = [
                r"(\bunion\b.*\bselect\b)",
                r"(\bor\b\s+1\s*=\s*1)",
                r"('.*--)",
                r"(\bdrop\b.*\btable\b)",
            ]
            for pattern in sql_patterns:
                if re.search(pattern, query_string, re.IGNORECASE):
                    return 100

            # Path traversal patterns
            if "../" in query_string or "..\\" in query_string:
                return 90

        return 0

    def _check_ua_anomaly(self, request, bot_verified: Optional[bool]) -> int:
        """
        Evaluate User-Agent string for anomalies.

        Checks for:
        - Empty User-Agent (highly suspicious)
        - Known scanner/attack tool signatures
        - Bot impersonation (claims to be a bot but fails verification)

        Args:
            request: Django HttpRequest object.
            bot_verified: Bot verification result.
                          True = verified, False = impersonation, None = not a bot.

        Returns:
            Score between 0 (normal) and 100 (highly suspicious).
        """
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Empty User-Agent is highly suspicious
        if not user_agent:
            return 100

        # Very short User-Agent (less than 10 chars)
        if len(user_agent) < 10:
            return 70

        # Check for known scanner User-Agents
        for pattern in _SCANNER_UA_RE:
            if pattern.search(user_agent):
                return 80

        # Bot impersonation: UA claims to be a bot but verification failed
        if bot_verified is False:
            return 80

        return 0

    def _calculate_weighted_score(self, signals: dict) -> int:
        """
        Calculate the weighted composite score from individual signals.

        Args:
            signals: Dict mapping signal names to their scores (0-100).

        Returns:
            Weighted composite score, clamped to 0-100.
        """
        total = 0.0
        for signal_name, weight in self.SIGNAL_WEIGHTS.items():
            signal_value = signals.get(signal_name, 0)
            total += signal_value * weight

        return max(0, min(100, int(round(total))))

    def _determine_action(self, total_score: int) -> str:
        """
        Determine the recommended action based on the total risk score.

        Score ranges and corresponding actions:
        - < threshold_log (30):        'pass'    - Allow normally
        - threshold_log to challenge:  'log'     - Allow but log
        - threshold_challenge to block:'challenge'- Consider challenging
        - >= threshold_block (80):     'block'   - Block the request

        Args:
            total_score: Composite risk score (0-100).

        Returns:
            Action string: 'pass', 'log', 'challenge', or 'block'.
        """
        if total_score >= self.threshold_block:
            return "block"
        elif total_score >= self.threshold_challenge:
            return "challenge"
        elif total_score >= self.threshold_log:
            return "log"
        else:
            return "pass"
