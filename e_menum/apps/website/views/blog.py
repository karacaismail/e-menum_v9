"""Blog views."""
import logging

from django.http import Http404
from django.views.generic import DetailView, ListView

from .mixins import CmsContextMixin
from ..models import BlogPost

logger = logging.getLogger(__name__)


class BlogView(CmsContextMixin, ListView):
    """Blog — published posts list."""
    template_name = 'website/blog.html'
    context_object_name = 'posts'
    paginate_by = 12
    page_slug = 'blog'

    def get_queryset(self):
        return BlogPost.objects.filter(
            status='published', deleted_at__isnull=True,
        ).order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Also get drafts for "coming soon" display if no published posts
        if not context['posts']:
            context['draft_posts'] = BlogPost.objects.filter(
                status='draft', deleted_at__isnull=True,
            ).order_by('-created_at')[:3]
        return context


class BlogDetailView(CmsContextMixin, DetailView):
    """Blog post detail page."""
    template_name = 'website/blog_detail.html'
    context_object_name = 'post'
    page_slug = 'blog'

    def get_queryset(self):
        return BlogPost.objects.filter(
            status='published', deleted_at__isnull=True,
        )

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            return queryset.get(slug=slug)
        except BlogPost.DoesNotExist:
            raise Http404
