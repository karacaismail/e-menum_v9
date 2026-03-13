"""
Add TrackingIntegration and CoreWebVitalsSnapshot models.

TrackingIntegration manages third-party tracking pixels and analytics scripts.
CoreWebVitalsSnapshot stores point-in-time Core Web Vitals measurements.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("seo", "0002_crawlreport_notfound404log"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackingIntegration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Human-readable name for this integration",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "platform",
                    models.CharField(
                        choices=[
                            ("gtm", "Google Tag Manager"),
                            ("ga4", "Google Analytics 4"),
                            ("meta_pixel", "Meta Pixel"),
                            ("tiktok_pixel", "TikTok Pixel"),
                            ("linkedin_insight", "LinkedIn Insight Tag"),
                            ("twitter_pixel", "Twitter/X Pixel"),
                            ("hotjar", "Hotjar"),
                            ("clarity", "Microsoft Clarity"),
                            ("custom_head", "Custom Head Script"),
                            ("custom_body", "Custom Body Script"),
                        ],
                        help_text="Tracking platform type",
                        max_length=30,
                        verbose_name="Platform",
                    ),
                ),
                (
                    "tracking_id",
                    models.CharField(
                        blank=True,
                        help_text="Platform-specific ID (e.g., GTM-XXXXX, G-XXXXX, pixel ID)",
                        max_length=200,
                        verbose_name="Tracking ID",
                    ),
                ),
                (
                    "custom_script",
                    models.TextField(
                        blank=True,
                        help_text="Custom JavaScript code (for custom_head/custom_body platforms)",
                        verbose_name="Custom Script",
                    ),
                ),
                (
                    "position",
                    models.CharField(
                        choices=[
                            ("head", "Head (<head>)"),
                            ("body_start", "Body Start (after <body>)"),
                            ("body_end", "Body End (before </body>)"),
                        ],
                        default="head",
                        help_text="Where in the HTML the script should be injected",
                        max_length=20,
                        verbose_name="Injection Position",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Only active integrations are injected into pages",
                        verbose_name="Active",
                    ),
                ),
                (
                    "environments",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text='Limit to specific environments, e.g. ["production"]. Empty = all.',
                        verbose_name="Environments",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Updated",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tracking Integration",
                "verbose_name_plural": "Tracking Integrations",
                "db_table": "seo_tracking_integrations",
                "ordering": ["platform", "name"],
            },
        ),
        migrations.CreateModel(
            name="CoreWebVitalsSnapshot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "url",
                    models.URLField(
                        help_text="Page URL measured",
                        verbose_name="URL",
                    ),
                ),
                (
                    "lcp",
                    models.FloatField(
                        blank=True,
                        help_text="Largest Contentful Paint in milliseconds",
                        null=True,
                        verbose_name="LCP (ms)",
                    ),
                ),
                (
                    "fid",
                    models.FloatField(
                        blank=True,
                        help_text="First Input Delay in milliseconds",
                        null=True,
                        verbose_name="FID (ms)",
                    ),
                ),
                (
                    "cls",
                    models.FloatField(
                        blank=True,
                        help_text="Cumulative Layout Shift score",
                        null=True,
                        verbose_name="CLS",
                    ),
                ),
                (
                    "ttfb",
                    models.FloatField(
                        blank=True,
                        help_text="Time to First Byte in milliseconds",
                        null=True,
                        verbose_name="TTFB (ms)",
                    ),
                ),
                (
                    "inp",
                    models.FloatField(
                        blank=True,
                        help_text="Interaction to Next Paint in milliseconds",
                        null=True,
                        verbose_name="INP (ms)",
                    ),
                ),
                (
                    "performance_score",
                    models.IntegerField(
                        blank=True,
                        help_text="Lighthouse performance score (0-100)",
                        null=True,
                        verbose_name="Performance Score",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        default="lighthouse",
                        help_text="Measurement source: 'crux' or 'lighthouse'",
                        max_length=20,
                        verbose_name="Source",
                    ),
                ),
                (
                    "measured_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Measured at",
                    ),
                ),
            ],
            options={
                "verbose_name": "Core Web Vitals Snapshot",
                "verbose_name_plural": "Core Web Vitals Snapshots",
                "db_table": "seo_cwv_snapshots",
                "ordering": ["-measured_at"],
                "indexes": [
                    models.Index(
                        fields=["url", "-measured_at"],
                        name="seo_cwv_sna_url_d160c8_idx",
                    ),
                ],
            },
        ),
    ]
