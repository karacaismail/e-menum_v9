"""
RSS and Atom feed generators for E-Menum public content.

Provides syndication feeds for blog posts, press releases, and other
public content. Uses Django's built-in syndication framework.

Feeds:
    LatestBlogPostsFeed   - RSS 2.0 feed of recent blog posts
    LatestBlogPostsAtom   - Atom 1.0 feed of recent blog posts

URL patterns:
    /feed/rss/   - RSS 2.0
    /feed/atom/  - Atom 1.0
"""

import logging

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

logger = logging.getLogger("apps.seo")


class LatestBlogPostsFeed(Feed):
    """RSS 2.0 feed of the latest blog posts."""

    title = "E-Menum Blog"
    description = "En son blog yazilari ve dijital menu haberleri"
    link = "/blog/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = getattr(settings, "SEO_SITE_NAME", "E-Menum") + " Blog"

    def items(self):
        """Return the latest 20 published blog posts."""
        try:
            from apps.website.models import BlogPost

            return (
                BlogPost.objects.filter(
                    is_published=True,
                    deleted_at__isnull=True,
                )
                .select_related("author")
                .order_by("-published_at")[:20]
            )
        except Exception:
            logger.exception("Failed to fetch blog posts for RSS feed")
            return []

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return (
            getattr(item, "excerpt", "") or getattr(item, "meta_description", "") or ""
        )

    def item_link(self, item):
        slug = getattr(item, "slug", "")
        return f"/blog/{slug}/"

    def item_pubdate(self, item):
        return getattr(item, "published_at", None) or getattr(item, "created_at", None)

    def item_author_name(self, item):
        author = getattr(item, "author", None)
        if author:
            return author.get_full_name() or str(author)
        return ""

    def item_categories(self, item):
        """Return tags or categories if available."""
        tags = getattr(item, "tags", None)
        if tags and hasattr(tags, "all"):
            return [str(tag) for tag in tags.all()]
        return []


class LatestBlogPostsAtomFeed(LatestBlogPostsFeed):
    """Atom 1.0 feed of the latest blog posts."""

    feed_type = Atom1Feed
    subtitle = LatestBlogPostsFeed.description
