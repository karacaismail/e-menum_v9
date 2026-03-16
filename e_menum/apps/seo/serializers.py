"""
DRF serializers for the SEO application.

Provides serializers for SEO models used by the admin panel API.
"""

from rest_framework import serializers

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


class RedirectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Redirect
        fields = [
            "id",
            "organization",
            "source_path",
            "target_url",
            "redirect_type",
            "is_active",
            "hit_count",
            "is_regex",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "hit_count",
            "created_at",
            "updated_at",
        ]


class AuthorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorProfile
        fields = [
            "id",
            "organization",
            "user",
            "display_name",
            "slug",
            "bio",
            "avatar_url",
            "social_links",
            "expertise_areas",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "slug", "created_at", "updated_at"]


class BrokenLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrokenLink
        fields = [
            "id",
            "organization",
            "source_url",
            "target_url",
            "status_code",
            "first_detected",
            "last_checked",
            "check_count",
            "is_resolved",
            "resolved_at",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "created_at"]


class TXTFileConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TXTFileConfig
        fields = [
            "id",
            "organization",
            "file_type",
            "content",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class PSEOTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PSEOTemplate
        fields = [
            "id",
            "organization",
            "name",
            "slug",
            "url_pattern",
            "title_template",
            "description_template",
            "body_template",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "slug", "created_at", "updated_at"]


class PSEOPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PSEOPage
        fields = [
            "id",
            "organization",
            "template",
            "slug",
            "title",
            "generated_url",
            "variables",
            "status",
            "is_indexed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class NotFound404LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotFound404Log
        fields = [
            "id",
            "organization",
            "path",
            "referrer",
            "user_agent",
            "ip_address",
            "hit_count",
            "first_seen",
            "last_seen",
            "is_resolved",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "created_at"]


class CrawlReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlReport
        fields = [
            "id",
            "organization",
            "crawler",
            "status",
            "pages_crawled",
            "errors_found",
            "warnings_found",
            "started_at",
            "completed_at",
            "summary",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "created_at"]


class TrackingIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingIntegration
        fields = [
            "id",
            "organization",
            "name",
            "integration_type",
            "tracking_id",
            "is_active",
            "config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class CoreWebVitalsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoreWebVitalsSnapshot
        fields = [
            "id",
            "organization",
            "url",
            "device_type",
            "lcp",
            "fid",
            "cls",
            "inp",
            "ttfb",
            "fcp",
            "score",
            "measured_at",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "created_at"]
