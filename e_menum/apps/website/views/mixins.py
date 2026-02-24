"""Shared view mixins for website pages."""
from ..models import PageHero


class CmsContextMixin:
    """
    Mixin that injects the PageHero for the current page into context.

    Subclasses set `page_slug` (e.g., 'home', 'features') to indicate
    which hero to load. Hero data falls back to defaults if not found.
    """
    page_slug = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.page_slug:
            hero = PageHero.objects.filter(page=self.page_slug, is_active=True).first()
            context['hero'] = hero
        return context
