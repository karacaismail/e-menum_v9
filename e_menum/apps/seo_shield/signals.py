"""
SEO Shield signal handlers.

Listens to events from core event bus and triggers Shield actions.
"""

from django.db import models
from django.dispatch import receiver

from apps.core.events import shield_threat_detected, shield_ip_blocked


@receiver(shield_threat_detected)
def on_threat_detected(sender, ip_address=None, risk_score=None, signals=None, action=None, **kwargs):
    """Update IP risk score when a threat is detected."""
    from apps.seo_shield.models import IPRiskScore
    obj, created = IPRiskScore.objects.get_or_create(
        ip_address=ip_address,
        defaults={'risk_score': risk_score or 0, 'signals': signals or {}},
    )
    if not created:
        obj.risk_score = risk_score or obj.risk_score
        if signals:
            obj.signals.update(signals)
        obj.total_requests += 1
        obj.save(update_fields=['risk_score', 'signals', 'total_requests', 'updated_at'])


@receiver(shield_ip_blocked)
def on_ip_blocked(sender, ip_address=None, reason=None, risk_score=None, **kwargs):
    """Increment blocked request count."""
    from apps.seo_shield.models import IPRiskScore
    IPRiskScore.objects.filter(ip_address=ip_address).update(
        blocked_requests=models.F('blocked_requests') + 1,
    )
