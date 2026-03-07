"""
Main SEO Shield middleware for Django.

Intercepts every incoming request and runs it through the Shield
pipeline: rate limiting, bot verification, and multi-signal risk
evaluation. Malicious or suspicious traffic is blocked or logged
based on configurable thresholds.

Pipeline:
1. Check SHIELD_ENABLED setting (skip if disabled)
2. Extract client IP
3. Check IP whitelist (skip if whitelisted)
4. Rate limit check
5. Bot verification (if UA matches a known bot pattern)
6. Multi-signal risk evaluation
7. Take action: pass, log, challenge, or block

Configuration (in Django settings):
- SHIELD_ENABLED: bool (default: True)
- SHIELD_WHITELIST_IPS: list of IPs to skip (default: [])
- SHIELD_RATE_LIMIT_WINDOW: int seconds (default: 60)
- SHIELD_RATE_LIMIT_MAX: int requests (default: 60)
- SHIELD_BLOCK_THRESHOLD: int 0-100 (default: 80)

Usage in settings.py MIDDLEWARE:
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        ...
        'apps.seo_shield.middleware.SEOShieldMiddleware',
        ...
    ]
"""

import json
import logging

from django.conf import settings
from django.http import HttpResponse

from apps.seo_shield.bot_verifier import BotVerifier
from apps.seo_shield.ip_reputation import IPReputationManager
from apps.seo_shield.rate_limiter import RateLimiter
from apps.seo_shield.risk_engine import RiskEngine

logger = logging.getLogger("apps.seo_shield")


class SEOShieldMiddleware:
    """
    Django middleware that protects the application from malicious
    traffic using multi-signal risk evaluation.
    """

    def __init__(self, get_response):
        """
        Initialize the middleware and its component services.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response
        self.rate_limiter = RateLimiter()
        self.bot_verifier = BotVerifier()
        self.ip_reputation = IPReputationManager()
        self.risk_engine = RiskEngine()

    def __call__(self, request):
        """
        Process an incoming request through the Shield pipeline.

        Args:
            request: Django HttpRequest object.

        Returns:
            HttpResponse from the downstream view, or a 429 response
            if the request is blocked.
        """
        # Step 1: Check if Shield is enabled
        if not getattr(settings, "SHIELD_ENABLED", True):
            return self.get_response(request)

        # Step 2: Extract client IP
        ip_address = self.rate_limiter.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Step 3: Check whitelist (settings-based and DB-based)
        whitelist_ips = getattr(settings, "SHIELD_WHITELIST_IPS", [])
        if ip_address in whitelist_ips:
            return self.get_response(request)

        if self.ip_reputation.is_whitelisted(ip_address):
            return self.get_response(request)

        # Step 4: Rate limit check
        rate_window = getattr(settings, "SHIELD_RATE_LIMIT_WINDOW", 60)
        rate_max = getattr(settings, "SHIELD_RATE_LIMIT_MAX", 60)
        is_limited, current_count, remaining = self.rate_limiter.is_rate_limited(
            ip_address,
            window=rate_window,
            max_requests=rate_max,
        )

        if is_limited:
            # Update IP reputation with rate limit signal
            self.ip_reputation.update_signal(ip_address, "rate_limit", 100)

            self._log_block(
                request=request,
                ip=ip_address,
                reason="rate_limit",
                risk_score=100,
                signals={"rate_limit": 100},
                action_taken="blocked",
                response_code=429,
            )

            logger.warning(
                "Rate limited: IP=%s requests=%d/%d window=%ds path=%s",
                ip_address,
                current_count,
                rate_max,
                rate_window,
                request.path,
            )

            return self._get_response_429()

        # Step 5: Bot verification
        bot_verified = None  # None means UA did not match any bot
        bot_name = None

        if user_agent:
            is_verified, bot_name = self.bot_verifier.verify_bot(ip_address, user_agent)

            if bot_name is not None:
                # UA matched a known bot pattern
                bot_verified = is_verified

                if not is_verified:
                    # Bot impersonation detected
                    self.ip_reputation.update_signal(ip_address, "ua_anomaly", 80)
                    logger.warning(
                        "Bot impersonation detected: IP=%s claims=%s UA=%s",
                        ip_address,
                        bot_name,
                        user_agent[:200],
                    )

        # Step 6: Multi-signal risk evaluation
        result = self.risk_engine.evaluate(
            request=request,
            ip_address=ip_address,
            rate_limited=is_limited,
            bot_verified=bot_verified,
        )

        # Update IP reputation signals from the evaluation
        for signal_name, signal_value in result.signals.items():
            if signal_value > 0:
                self.ip_reputation.update_signal(
                    ip_address,
                    signal_name,
                    signal_value,
                )

        # Step 7: Take action based on risk evaluation
        if result.action == "block":
            self._log_block(
                request=request,
                ip=ip_address,
                reason="risk_threshold",
                risk_score=result.score,
                signals=result.signals,
                action_taken="blocked",
                response_code=429,
            )

            # Fire the shield_threat_detected event
            from apps.core.events import shield_threat_detected

            shield_threat_detected.send(
                sender=self.__class__,
                ip_address=ip_address,
                risk_score=result.score,
                signals=result.signals,
                action="block",
            )

            logger.warning(
                "Blocked: IP=%s score=%d action=%s path=%s signals=%s",
                ip_address,
                result.score,
                result.action,
                request.path,
                result.signals,
            )

            return self._get_response_429()

        if result.action == "challenge":
            # For now, challenge acts the same as block.
            # Future: serve a CAPTCHA or JS challenge page.
            self._log_block(
                request=request,
                ip=ip_address,
                reason="risk_challenge",
                risk_score=result.score,
                signals=result.signals,
                action_taken="challenged",
                response_code=429,
            )

            from apps.core.events import shield_threat_detected

            shield_threat_detected.send(
                sender=self.__class__,
                ip_address=ip_address,
                risk_score=result.score,
                signals=result.signals,
                action="challenge",
            )

            logger.warning(
                "Challenged: IP=%s score=%d path=%s signals=%s",
                ip_address,
                result.score,
                request.path,
                result.signals,
            )

            return self._get_response_429()

        if result.action == "log":
            self._log_block(
                request=request,
                ip=ip_address,
                reason="risk_elevated",
                risk_score=result.score,
                signals=result.signals,
                action_taken="logged",
                response_code=200,
            )

            logger.info(
                "Logged suspicious: IP=%s score=%d path=%s signals=%s",
                ip_address,
                result.score,
                request.path,
                result.signals,
            )

        # Pass through
        return self.get_response(request)

    def _log_block(
        self,
        request,
        ip: str,
        reason: str,
        risk_score: int,
        signals: dict,
        action_taken: str,
        response_code: int,
    ):
        """
        Create a BlockLog entry for audit trail.

        Args:
            request: Django HttpRequest object.
            ip: Client IP address.
            reason: Short reason code (e.g., 'rate_limit', 'risk_threshold').
            risk_score: The composite risk score at time of action.
            signals: Signal breakdown dict.
            action_taken: Action taken ('blocked', 'challenged', 'logged').
            response_code: HTTP response code returned to the client.
        """
        try:
            from apps.seo_shield.models import BlockLog

            BlockLog.objects.create(
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                path=request.path[:500],
                method=request.method[:10],
                reason=reason[:50],
                risk_score=risk_score,
                signals=signals,
                action_taken=action_taken,
                response_code=response_code,
            )
        except Exception as exc:
            logger.error(
                "Failed to create BlockLog entry: %s",
                exc,
            )

    @staticmethod
    def _get_response_429() -> HttpResponse:
        """
        Return a 429 Too Many Requests response with a JSON body.

        Returns:
            HttpResponse with status 429 and JSON error body.
        """
        body = json.dumps(
            {
                "success": False,
                "error": {
                    "code": "TOO_MANY_REQUESTS",
                    "message": "Too Many Requests",
                },
            }
        )
        return HttpResponse(
            content=body,
            content_type="application/json",
            status=429,
        )
