"""
DRF ViewSets for the SEO application.

Provides ViewSets for managing SEO configuration, redirects,
author profiles, pSEO templates/pages, and monitoring data.
All use BaseTenantViewSet for automatic organization filtering.
"""

from shared.views.base import BaseTenantReadOnlyViewSet, BaseTenantViewSet

from apps.seo.models import (
    AuthorProfile,
    BrokenLink,
    CoreWebVitalsSnapshot,
    CrawlReport,
    NotFound404Log,
    PSEOPage,
    PSEOTemplate,
    Redirect,
    TrackingIntegration,
    TXTFileConfig,
)
from apps.seo.serializers import (
    AuthorProfileSerializer,
    BrokenLinkSerializer,
    CoreWebVitalsSnapshotSerializer,
    CrawlReportSerializer,
    NotFound404LogSerializer,
    PSEOPageSerializer,
    PSEOTemplateSerializer,
    RedirectSerializer,
    TrackingIntegrationSerializer,
    TXTFileConfigSerializer,
)


class RedirectViewSet(BaseTenantViewSet):
    """ViewSet for URL redirect management."""

    queryset = Redirect.objects.all()
    serializer_class = RedirectSerializer
    permission_resource = "seo"
    filterset_fields = ["redirect_type", "is_active"]
    search_fields = ["source_path", "target_url", "notes"]


class AuthorProfileViewSet(BaseTenantViewSet):
    """ViewSet for author profile management (E-E-A-T)."""

    queryset = AuthorProfile.objects.select_related("user").all()
    serializer_class = AuthorProfileSerializer
    permission_resource = "seo"
    search_fields = ["display_name", "bio"]


class BrokenLinkViewSet(BaseTenantReadOnlyViewSet):
    """Read-only ViewSet for broken link monitoring."""

    queryset = BrokenLink.objects.all()
    serializer_class = BrokenLinkSerializer
    permission_resource = "seo"
    filterset_fields = ["is_resolved", "status_code"]


class TXTFileConfigViewSet(BaseTenantViewSet):
    """ViewSet for robots.txt, humans.txt, etc. configuration."""

    queryset = TXTFileConfig.objects.all()
    serializer_class = TXTFileConfigSerializer
    permission_resource = "seo"
    filterset_fields = ["file_type", "is_active"]


class PSEOTemplateViewSet(BaseTenantViewSet):
    """ViewSet for programmatic SEO page templates."""

    queryset = PSEOTemplate.objects.all()
    serializer_class = PSEOTemplateSerializer
    permission_resource = "seo"
    search_fields = ["name", "url_pattern"]


class PSEOPageViewSet(BaseTenantViewSet):
    """ViewSet for generated programmatic SEO pages."""

    queryset = PSEOPage.objects.select_related("template").all()
    serializer_class = PSEOPageSerializer
    permission_resource = "seo"
    filterset_fields = ["template", "status", "is_indexed"]
    search_fields = ["title", "slug"]


class NotFound404LogViewSet(BaseTenantReadOnlyViewSet):
    """Read-only ViewSet for 404 error monitoring."""

    queryset = NotFound404Log.objects.all()
    serializer_class = NotFound404LogSerializer
    permission_resource = "seo"
    filterset_fields = ["is_resolved"]
    search_fields = ["path", "referrer"]


class CrawlReportViewSet(BaseTenantReadOnlyViewSet):
    """Read-only ViewSet for crawl report data."""

    queryset = CrawlReport.objects.all()
    serializer_class = CrawlReportSerializer
    permission_resource = "seo"
    filterset_fields = ["crawler", "status"]


class TrackingIntegrationViewSet(BaseTenantViewSet):
    """ViewSet for tracking integration management (GA, GTM, etc.)."""

    queryset = TrackingIntegration.objects.all()
    serializer_class = TrackingIntegrationSerializer
    permission_resource = "seo"
    filterset_fields = ["integration_type", "is_active"]


class CoreWebVitalsSnapshotViewSet(BaseTenantReadOnlyViewSet):
    """Read-only ViewSet for Core Web Vitals monitoring data."""

    queryset = CoreWebVitalsSnapshot.objects.all()
    serializer_class = CoreWebVitalsSnapshotSerializer
    permission_resource = "seo"
    filterset_fields = ["device_type", "url"]
