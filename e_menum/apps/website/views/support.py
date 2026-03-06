"""Support / Help center views."""
import logging

from django.http import Http404
from django.views.generic import DetailView, ListView

from .mixins import CmsContextMixin
from ..models import FAQ, HelpArticle, HelpCategory

logger = logging.getLogger(__name__)


class SupportView(CmsContextMixin, ListView):
    """Help center index — categories overview."""
    template_name = 'website/support/index.html'
    context_object_name = 'categories'
    page_slug = 'support'

    def get_queryset(self):
        return HelpCategory.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['popular_articles'] = HelpArticle.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('-view_count')[:6]
        context['faqs'] = FAQ.objects.filter(
            is_active=True, deleted_at__isnull=True,
            page__in=['support', 'both'],
        ).order_by('sort_order')
        return context


class HelpCategoryView(CmsContextMixin, DetailView):
    """Help category with its articles."""
    template_name = 'website/support/category.html'
    context_object_name = 'category'
    page_slug = 'support'

    def get_queryset(self):
        return HelpCategory.objects.filter(is_active=True, deleted_at__isnull=True)

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            obj = queryset.get(slug=slug)
        except HelpCategory.DoesNotExist:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles'] = HelpArticle.objects.filter(
            category=self.object, is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')
        return context


class HelpArticleView(CmsContextMixin, DetailView):
    """Help article detail — increments view_count."""
    template_name = 'website/support/article.html'
    context_object_name = 'article'
    page_slug = 'support'

    def get_queryset(self):
        return HelpArticle.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).select_related('category')

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('article_slug')
        try:
            obj = queryset.get(slug=slug)
        except HelpArticle.DoesNotExist:
            raise Http404
        # Increment view count
        HelpArticle.objects.filter(pk=obj.pk).update(view_count=obj.view_count + 1)
        return obj
