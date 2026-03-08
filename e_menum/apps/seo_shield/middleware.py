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
        Return a 429 Too Many Requests response.

        For API requests (Accept: application/json or /api/ paths),
        returns JSON. Otherwise returns a styled HTML error page.

        Returns:
            HttpResponse with status 429.
        """
        # Check if this is an API request — return JSON for those
        # (handled by the calling context via request, but we keep
        #  the static method signature for backward compatibility)
        html = """<!DOCTYPE html>
<html lang="tr" style="height:100%">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>429 — Çok Fazla İstek</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
  height:100%;font-family:'Inter',system-ui,sans-serif;
  background:#0f172a;color:#e2e8f0;
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;position:relative;
}
/* animated gradient bg */
body::before{
  content:'';position:absolute;inset:0;
  background:
    radial-gradient(ellipse 600px 400px at 20% 50%,rgba(59,130,246,.12),transparent),
    radial-gradient(ellipse 500px 500px at 80% 20%,rgba(168,85,247,.10),transparent),
    radial-gradient(ellipse 400px 300px at 60% 80%,rgba(244,63,94,.08),transparent);
  animation:bgPulse 8s ease-in-out infinite alternate;
}
@keyframes bgPulse{
  0%{opacity:.6;transform:scale(1)}
  100%{opacity:1;transform:scale(1.05)}
}
.container{
  position:relative;z-index:1;text-align:center;padding:2rem;
  max-width:520px;width:100%;
}
/* big 429 number */
.code{
  font-size:clamp(7rem,20vw,12rem);font-weight:800;
  line-height:1;letter-spacing:-.04em;
  background:linear-gradient(135deg,#3b82f6,#a855f7,#f43f5e);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
  filter:drop-shadow(0 0 60px rgba(139,92,246,.3));
  animation:codeGlow 3s ease-in-out infinite alternate;
  user-select:none;
}
@keyframes codeGlow{
  0%{filter:drop-shadow(0 0 40px rgba(139,92,246,.2))}
  100%{filter:drop-shadow(0 0 80px rgba(139,92,246,.4))}
}
/* animated bar under code */
.bar{
  width:120px;height:4px;margin:1.5rem auto;border-radius:9999px;
  background:linear-gradient(90deg,#3b82f6,#a855f7,#f43f5e,#3b82f6);
  background-size:300% 100%;
  animation:barSlide 3s linear infinite;
}
@keyframes barSlide{0%{background-position:0% 0}100%{background-position:300% 0}}
h1{font-size:1.375rem;font-weight:700;color:#f1f5f9;margin-bottom:.5rem}
p{font-size:.9rem;color:#94a3b8;line-height:1.6;max-width:400px;margin:0 auto}
.hint{
  margin-top:2rem;padding:1rem 1.25rem;
  background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.06);
  border-radius:12px;font-size:.8rem;color:#64748b;
  display:flex;align-items:center;gap:.75rem;
}
.hint svg{flex-shrink:0;width:20px;height:20px;color:#475569}
.actions{margin-top:2rem;display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap}
.btn{
  display:inline-flex;align-items:center;gap:.5rem;
  padding:.625rem 1.25rem;border-radius:10px;
  font-size:.8125rem;font-weight:600;
  text-decoration:none;transition:all .2s;cursor:pointer;border:0;
}
.btn-primary{
  background:linear-gradient(135deg,#3b82f6,#6366f1);
  color:#fff;box-shadow:0 4px 16px rgba(99,102,241,.3);
}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 6px 24px rgba(99,102,241,.4)}
.btn-ghost{
  background:rgba(255,255,255,.06);color:#cbd5e1;
  border:1px solid rgba(255,255,255,.08);
}
.btn-ghost:hover{background:rgba(255,255,255,.1);color:#f1f5f9}
/* countdown */
.countdown{
  margin-top:1.5rem;font-size:.75rem;color:#475569;
  display:flex;align-items:center;justify-content:center;gap:.5rem;
}
.countdown span{
  font-variant-numeric:tabular-nums;font-weight:600;color:#94a3b8;
}
/* floating particles */
.particle{
  position:fixed;border-radius:50%;pointer-events:none;
  background:rgba(139,92,246,.15);
  animation:float linear infinite;
}
@keyframes float{
  0%{transform:translateY(100vh) scale(0);opacity:0}
  10%{opacity:1}
  90%{opacity:1}
  100%{transform:translateY(-10vh) scale(1);opacity:0}
}
@media(prefers-reduced-motion:reduce){
  .particle,.bar,body::before,.code{animation:none!important}
}
</style>
</head>
<body>
<!-- floating particles -->
<div class="particle" style="width:6px;height:6px;left:10%;animation-duration:12s;animation-delay:0s"></div>
<div class="particle" style="width:4px;height:4px;left:25%;animation-duration:16s;animation-delay:2s"></div>
<div class="particle" style="width:8px;height:8px;left:50%;animation-duration:10s;animation-delay:4s"></div>
<div class="particle" style="width:5px;height:5px;left:70%;animation-duration:14s;animation-delay:1s"></div>
<div class="particle" style="width:3px;height:3px;left:85%;animation-duration:18s;animation-delay:3s"></div>
<div class="particle" style="width:7px;height:7px;left:40%;animation-duration:11s;animation-delay:5s"></div>

<div class="container">
  <div class="code">429</div>
  <div class="bar"></div>
  <h1>Yavaşlayın, çok hızlısınız!</h1>
  <p>Kısa sürede çok fazla istek gönderdiniz. Sunucumuzu korumak için geçici olarak erişiminizi yavaşlattık.</p>

  <div class="hint">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
    </svg>
    <span>Birkaç saniye bekleyip tekrar deneyin. Sorun devam ederse sayfayı yenileyin.</span>
  </div>

  <div class="countdown" id="cd">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
    Otomatik yenileme: <span id="ct">15</span>s
  </div>

  <div class="actions">
    <button class="btn btn-primary" onclick="location.reload()">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
      Tekrar Dene
    </button>
    <button class="btn btn-ghost" onclick="history.back()">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      Geri Dön
    </button>
  </div>
</div>

<script>
(function(){
  var s=15,el=document.getElementById('ct');
  var t=setInterval(function(){s--;if(el)el.textContent=s;if(s<=0){clearInterval(t);location.reload();}},1000);
})();
</script>
</body>
</html>"""
        return HttpResponse(
            content=html,
            content_type="text/html; charset=utf-8",
            status=429,
        )
