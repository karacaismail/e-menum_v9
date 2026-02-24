"""
SEO URL configuration for E-Menum.

Maps TXT file endpoints (robots.txt, humans.txt, security.txt, ads.txt,
llms.txt) and the XML sitemap to their respective views.
"""

from django.urls import path
from django.contrib.sitemaps.views import sitemap

from apps.seo import txt_files
from apps.seo.sitemaps import sitemaps

app_name = 'seo'

urlpatterns = [
    # TXT files
    path('robots.txt', txt_files.robots_txt_view, name='robots-txt'),
    path('humans.txt', txt_files.humans_txt_view, name='humans-txt'),
    path('security.txt', txt_files.security_txt_view, name='security-txt'),
    path('.well-known/security.txt', txt_files.security_txt_view, name='security-txt-wellknown'),
    path('ads.txt', txt_files.ads_txt_view, name='ads-txt'),
    path('llms.txt', txt_files.llms_txt_view, name='llms-txt'),
    # Sitemaps
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
]
