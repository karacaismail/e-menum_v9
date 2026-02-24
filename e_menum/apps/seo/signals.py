"""
SEO signal handlers.

Listens to events from core event bus and triggers SEO actions.
"""

from django.dispatch import receiver

from apps.core.events import content_published, broken_link_found


@receiver(content_published)
def on_content_published(sender, instance=None, content_type=None, **kwargs):
    """Recalculate SEO score when content is published."""
    if instance and hasattr(instance, 'calculate_seo_score'):
        instance.calculate_seo_score()
        instance.save(update_fields=['seo_score', 'seo_suggestions', 'last_seo_analysis'])


@receiver(broken_link_found)
def on_broken_link_found(sender, source_url=None, target_url=None, status_code=None, **kwargs):
    """Log broken link detection event."""
    import logging
    logger = logging.getLogger('apps.seo')
    logger.warning('Broken link detected: %s -> %s (status: %s)', source_url, target_url, status_code)
