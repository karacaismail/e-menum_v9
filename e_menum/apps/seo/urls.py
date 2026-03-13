"""
SEO URL configuration for E-Menum.

Maps TXT file endpoints (robots.txt, humans.txt, security.txt, ads.txt,
llms.txt), XML sitemaps, RSS/Atom feeds, and IndexNow key verification
to their respective views.
"""

from django.contrib.sitemaps.views import index as sitemap_index
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from apps.seo import txt_files
from apps.seo.feeds import LatestBlogPostsAtomFeed, LatestBlogPostsFeed
from apps.seo.sitemaps import sitemaps

app_name = "seo"

urlpatterns = [
    # TXT files
    path("robots.txt", txt_files.robots_txt_view, name="robots-txt"),
    path("humans.txt", txt_files.humans_txt_view, name="humans-txt"),
    path("security.txt", txt_files.security_txt_view, name="security-txt"),
    path(
        ".well-known/security.txt",
        txt_files.security_txt_view,
        name="security-txt-wellknown",
    ),
    path("ads.txt", txt_files.ads_txt_view, name="ads-txt"),
    path("llms.txt", txt_files.llms_txt_view, name="llms-txt"),
    # Sitemaps — index + per-section pattern
    path(
        "sitemap.xml",
        sitemap_index,
        {"sitemaps": sitemaps, "sitemap_url_name": "seo:sitemap-section"},
        name="sitemap-index",
    ),
    path(
        "sitemap-<section>.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="sitemap-section",
    ),
    # RSS / Atom feeds
    path("feed/rss/", LatestBlogPostsFeed(), name="feed-rss"),
    path("feed/atom/", LatestBlogPostsAtomFeed(), name="feed-atom"),
]
