"""
Shared event bus for inter-module communication using Django signals.

Modules communicate via events (signals) to stay loosely coupled.
No direct imports between apps/seo and apps/seo_shield — only events.
"""

import django.dispatch

# --- SEO Events ---
seo_content_updated = django.dispatch.Signal()
# Sent when SEO content is updated. Provides: instance, fields_changed

content_published = django.dispatch.Signal()
# Sent when content is published. Provides: instance, content_type

broken_link_found = django.dispatch.Signal()
# Sent when a broken link is detected. Provides: source_url, target_url, status_code

# --- Shield Events ---
shield_threat_detected = django.dispatch.Signal()
# Sent when a threat is detected. Provides: ip_address, risk_score, signals, action

shield_ip_blocked = django.dispatch.Signal()
# Sent when an IP is blocked. Provides: ip_address, reason, risk_score
