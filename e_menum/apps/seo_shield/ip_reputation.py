"""
IP reputation management for SEO Shield.

Tracks per-IP risk scores based on multiple weighted signals. Each signal
contributes to a composite risk score (0-100) that determines whether
traffic from an IP should be allowed, logged, challenged, or blocked.

Signal weights:
- rate_limit:       0.30  (rate limit violations)
- header_anomaly:   0.20  (missing or suspicious HTTP headers)
- path_pattern:     0.20  (suspicious URL path patterns)
- ua_anomaly:       0.15  (User-Agent anomalies)
- robots_violation: 0.15  (robots.txt violations)

Usage:
    manager = IPReputationManager()
    score = manager.get_risk_score('1.2.3.4')
    manager.update_signal('1.2.3.4', 'rate_limit', 100)
    if manager.is_blocked('1.2.3.4'):
        # Block the request
"""

import logging

from django.db.models import F

logger = logging.getLogger('apps.seo_shield')


class IPReputationManager:
    """
    Manages IP risk scores using weighted multi-signal scoring.

    Each IP address gets an IPRiskScore record in the database that
    tracks individual signal values and a composite risk score.
    """

    # Weights for each signal type. Must sum to 1.0.
    SIGNAL_WEIGHTS = {
        'rate_limit': 0.30,
        'header_anomaly': 0.20,
        'path_pattern': 0.20,
        'ua_anomaly': 0.15,
        'robots_violation': 0.15,
    }

    def get_risk_score(self, ip_address: str) -> int:
        """
        Get the current risk score for an IP address.

        Creates a new IPRiskScore entry with score 0 if the IP has
        not been seen before.

        Args:
            ip_address: The IP address to look up.

        Returns:
            Integer risk score between 0 and 100.
        """
        from apps.seo_shield.models import IPRiskScore

        obj, created = IPRiskScore.objects.get_or_create(
            ip_address=ip_address,
            defaults={
                'risk_score': 0,
                'signals': {},
                'total_requests': 1,
            },
        )

        if not created:
            # Increment total request count
            IPRiskScore.objects.filter(pk=obj.pk).update(
                total_requests=F('total_requests') + 1,
            )

        return obj.risk_score

    def update_signal(self, ip_address: str, signal_type: str, value: int) -> int:
        """
        Update a specific risk signal for an IP address.

        Updates the signal value, recalculates the composite risk score
        from all weighted signals, and saves to the database.

        Args:
            ip_address: The IP address to update.
            signal_type: Signal name (e.g., 'rate_limit', 'header_anomaly').
                         Must be a key in SIGNAL_WEIGHTS.
            value: Signal value between 0 and 100.

        Returns:
            The new composite risk score (0-100).
        """
        from apps.seo_shield.models import IPRiskScore

        if signal_type not in self.SIGNAL_WEIGHTS:
            logger.warning(
                "Unknown signal type '%s' for IP %s, ignoring",
                signal_type, ip_address,
            )
            return 0

        # Clamp value to 0-100
        value = max(0, min(100, value))

        obj, created = IPRiskScore.objects.get_or_create(
            ip_address=ip_address,
            defaults={
                'risk_score': 0,
                'signals': {signal_type: value},
                'total_requests': 0,
            },
        )

        if not created:
            # Update the specific signal in the signals dict
            signals = obj.signals or {}
            signals[signal_type] = value
            obj.signals = signals
        else:
            signals = obj.signals

        # Recalculate total risk score
        new_score = self.calculate_total_score(signals)
        obj.risk_score = new_score
        obj.save(update_fields=['risk_score', 'signals', 'updated_at'])

        logger.debug(
            "Updated signal '%s'=%d for IP %s, new risk_score=%d",
            signal_type, value, ip_address, new_score,
        )

        return new_score

    def calculate_total_score(self, signals: dict) -> int:
        """
        Calculate the weighted composite risk score from individual signals.

        Each signal value (0-100) is multiplied by its weight, and the
        results are summed. The final score is clamped to 0-100.

        Args:
            signals: Dict mapping signal names to their values (0-100).

        Returns:
            Integer composite risk score between 0 and 100.
        """
        if not signals:
            return 0

        total = 0.0
        for signal_name, weight in self.SIGNAL_WEIGHTS.items():
            signal_value = signals.get(signal_name, 0)
            # Ensure signal value is numeric and clamped
            try:
                signal_value = max(0, min(100, int(signal_value)))
            except (TypeError, ValueError):
                signal_value = 0
            total += signal_value * weight

        return max(0, min(100, int(round(total))))

    def decay_scores(self, decay_factor: float = 0.9) -> int:
        """
        Reduce all risk scores by a decay factor.

        Used for periodic cleanup so that IPs that stop misbehaving
        gradually return to a low risk score.

        Args:
            decay_factor: Multiplier applied to each signal value.
                          0.9 means scores decay by 10% per cycle.

        Returns:
            Number of IPRiskScore records updated.
        """
        from apps.seo_shield.models import IPRiskScore

        # Only decay records with non-zero scores
        records = IPRiskScore.objects.filter(risk_score__gt=0)
        updated_count = 0

        for record in records.iterator():
            signals = record.signals or {}
            decayed_signals = {}

            for signal_name, signal_value in signals.items():
                try:
                    new_value = int(float(signal_value) * decay_factor)
                except (TypeError, ValueError):
                    new_value = 0
                # Remove signals that have decayed to zero
                if new_value > 0:
                    decayed_signals[signal_name] = new_value

            new_score = self.calculate_total_score(decayed_signals)

            record.signals = decayed_signals
            record.risk_score = new_score
            record.save(update_fields=['risk_score', 'signals', 'updated_at'])
            updated_count += 1

        logger.info(
            "Decayed risk scores for %d IP records (factor=%.2f)",
            updated_count, decay_factor,
        )

        return updated_count

    def is_blocked(self, ip_address: str, threshold: int = 60) -> bool:
        """
        Check if an IP address should be blocked.

        An IP is blocked if:
        - Its risk_score >= threshold, OR
        - It is explicitly blacklisted (is_blacklisted=True)

        Args:
            ip_address: The IP address to check.
            threshold: Risk score threshold for blocking (default: 60).

        Returns:
            True if the IP should be blocked.
        """
        from apps.seo_shield.models import IPRiskScore

        try:
            record = IPRiskScore.objects.get(ip_address=ip_address)
            return record.is_blacklisted or record.risk_score >= threshold
        except IPRiskScore.DoesNotExist:
            return False

    def is_whitelisted(self, ip_address: str) -> bool:
        """
        Check if an IP address is explicitly whitelisted.

        Whitelisted IPs bypass all Shield checks.

        Args:
            ip_address: The IP address to check.

        Returns:
            True if the IP is whitelisted.
        """
        from apps.seo_shield.models import IPRiskScore

        try:
            record = IPRiskScore.objects.get(ip_address=ip_address)
            return record.is_whitelisted
        except IPRiskScore.DoesNotExist:
            return False
