"""
Celery tasks for the SEO application.

Periodic and on-demand tasks for SEO maintenance:
    - check_broken_links:      Full site broken link crawl and persistence
    - recalculate_seo_scores:  Recalculate SEO scores for all content
    - generate_pseo_pages:     Generate pSEO pages from a template
    - cleanup_old_redirects:   Soft-delete stale unused redirects
    - generate_txt_files:      Regenerate auto-generated TXT file configs

Task schedule (configured in config/celery.py):
    - check_broken_links:      weekly (Sunday 03:00 UTC)
    - recalculate_seo_scores:  daily at 04:00 UTC
    - cleanup_old_redirects:   monthly (1st of month, 05:00 UTC)
    - generate_txt_files:      daily at 04:30 UTC
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("apps.seo")


# =============================================================================
# BROKEN LINK CHECK
# =============================================================================


@shared_task(
    bind=True,
    name="seo.check_broken_links",
    max_retries=2,
    default_retry_delay=300,
    soft_time_limit=1800,
    time_limit=3600,
)
def check_broken_links(self):
    """
    Perform a full site crawl to detect broken links.

    Gets the base URL from SiteSettings (website_url field) or falls back
    to the SITE_URL setting. Creates a BrokenLinkChecker, runs a full site
    crawl, and persists results to the BrokenLink model.

    Returns:
        dict: Summary with pages_crawled, broken_links_found, and
              broken_links_saved counts.
    """
    from apps.seo.internal_links import BrokenLinkChecker

    # Determine base URL
    base_url = getattr(settings, "SITE_URL", None)
    if not base_url:
        try:
            from apps.website.models import SiteSettings

            site_settings = SiteSettings.load()
            base_url = getattr(site_settings, "website_url", None)
        except Exception:
            pass

    if not base_url:
        base_url = settings.SITE_URL
        logger.warning(
            "No SITE_URL or SiteSettings.website_url configured, falling back to %s",
            base_url,
        )

    logger.info("Starting broken link check for base URL: %s", base_url)

    # Create CrawlReport record
    from apps.seo.models import CrawlReport

    report = CrawlReport.objects.create(
        started_at=timezone.now(),
        status="running",
    )

    try:
        checker = BrokenLinkChecker(base_url=base_url, timeout=15)
        results = checker.full_site_crawl(max_pages=200)

        # Count broken/redirected/healthy links across all pages
        total_broken = 0
        total_redirected = 0
        total_healthy = 0
        total_links = 0
        for page_url, links in results.items():
            for link_url, status_code in links:
                total_links += 1
                if status_code == 0 or status_code >= 400:
                    total_broken += 1
                elif 300 <= status_code < 400:
                    total_redirected += 1
                else:
                    total_healthy += 1

        # Save results to database
        saved = checker.save_results(results)

        # Update CrawlReport
        report.finished_at = timezone.now()
        report.total_pages = len(results)
        report.total_links = total_links
        report.broken_count = total_broken
        report.redirected_count = total_redirected
        report.healthy_count = total_healthy
        report.status = "completed"
        report.save()

        summary = {
            "pages_crawled": len(results),
            "broken_links_found": total_broken,
            "broken_links_saved": saved,
            "crawl_report_id": str(report.pk),
        }
        logger.info(
            "Broken link check complete: %d pages crawled, "
            "%d broken links found, %d records saved",
            summary["pages_crawled"],
            summary["broken_links_found"],
            summary["broken_links_saved"],
        )
        return summary

    except Exception as exc:
        # Mark report as failed
        report.finished_at = timezone.now()
        report.status = "failed"
        report.error_message = str(exc)[:1000]
        report.save()
        logger.exception("Broken link check failed: %s", exc)
        raise self.retry(exc=exc)


# =============================================================================
# SEO SCORE RECALCULATION
# =============================================================================


@shared_task(
    bind=True,
    name="seo.recalculate_seo_scores",
    max_retries=2,
    default_retry_delay=120,
    soft_time_limit=600,
    time_limit=900,
)
def recalculate_seo_scores(self):
    """
    Recalculate SEO scores for all content models using the SEOMixin.

    Iterates all BlogPost and PSEOPage records that have not been
    soft-deleted, calls calculate_seo_score() on each, and saves the
    updated score and timestamp.

    Returns:
        dict: Summary with blogposts_processed and pseo_pages_processed counts.
    """
    from apps.seo.models import PSEOPage

    now = timezone.now()
    blogpost_count = 0
    pseo_count = 0

    # -- BlogPosts --
    try:
        from apps.website.models import BlogPost

        blogposts = BlogPost.objects.filter(deleted_at__isnull=True)

        for post in blogposts.iterator():
            try:
                post.calculate_seo_score()
                post.last_seo_analysis = now
                post.save(
                    update_fields=["seo_score", "last_seo_analysis", "updated_at"]
                )
                blogpost_count += 1
            except Exception as exc:
                logger.error(
                    "Failed to recalculate SEO score for BlogPost %s: %s",
                    post.pk,
                    exc,
                )
    except ImportError:
        logger.warning(
            "BlogPost model not available, skipping blog SEO score recalculation"
        )

    # -- PSEOPages --
    pseo_pages = PSEOPage.objects.filter(deleted_at__isnull=True)

    for page in pseo_pages.iterator():
        try:
            page.calculate_seo_score()
            page.last_seo_analysis = now
            page.save(update_fields=["seo_score", "last_seo_analysis", "updated_at"])
            pseo_count += 1
        except Exception as exc:
            logger.error(
                "Failed to recalculate SEO score for PSEOPage %s: %s",
                page.pk,
                exc,
            )

    summary = {
        "blogposts_processed": blogpost_count,
        "pseo_pages_processed": pseo_count,
    }
    logger.info(
        "SEO score recalculation complete: %d blog posts, %d pSEO pages processed",
        blogpost_count,
        pseo_count,
    )
    return summary


# =============================================================================
# PSEO PAGE GENERATION
# =============================================================================


@shared_task(
    bind=True,
    name="seo.generate_pseo_pages",
    max_retries=1,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=900,
)
def generate_pseo_pages(self, template_id: str):
    """
    Generate programmatic SEO pages from a template.

    Fetches the PSEOTemplate by ID, generates city x sector variable
    combinations using PSEOEngine, and creates PSEOPage records for
    each combination.

    Args:
        template_id: UUID string of the PSEOTemplate to generate from.

    Returns:
        dict: Summary with template_name and pages_created count.
    """
    from apps.seo.models import PSEOTemplate
    from apps.seo.pseo import PSEOEngine, generate_city_sector_combinations

    try:
        template = PSEOTemplate.objects.get(
            pk=template_id,
            is_active=True,
            deleted_at__isnull=True,
        )
    except PSEOTemplate.DoesNotExist:
        logger.error(
            "PSEOTemplate %s not found or inactive — skipping generation",
            template_id,
        )
        return {"template_id": template_id, "error": "Template not found or inactive"}

    logger.info("Starting pSEO page generation for template: %s", template.name)

    engine = PSEOEngine()
    variables_list = generate_city_sector_combinations()
    pages_created = engine.generate_pages(template, variables_list)

    summary = {
        "template_name": template.name,
        "template_id": str(template_id),
        "pages_created": pages_created,
        "total_combinations": len(variables_list),
    }
    logger.info(
        'pSEO generation complete for template "%s": %d pages created '
        "from %d combinations",
        template.name,
        pages_created,
        len(variables_list),
    )
    return summary


# =============================================================================
# REDIRECT CLEANUP
# =============================================================================


@shared_task(
    bind=True,
    name="seo.cleanup_old_redirects",
    max_retries=1,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def cleanup_old_redirects(self):
    """
    Soft-delete stale redirects that have never been used.

    Finds redirects with hit_count=0 that were created more than 90 days
    ago and have not been soft-deleted yet. Sets deleted_at to mark them
    as soft-deleted.

    Returns:
        dict: Summary with redirects_cleaned count.
    """
    from apps.seo.models import Redirect

    cutoff_date = timezone.now() - timedelta(days=90)

    stale_redirects = Redirect.objects.filter(
        hit_count=0,
        created_at__lt=cutoff_date,
        deleted_at__isnull=True,
    )

    count = stale_redirects.count()

    if count > 0:
        now = timezone.now()
        stale_redirects.update(deleted_at=now)
        logger.info(
            "Soft-deleted %d stale redirects (hit_count=0, created before %s)",
            count,
            cutoff_date.strftime("%Y-%m-%d"),
        )
    else:
        logger.info("No stale redirects found for cleanup")

    return {
        "redirects_cleaned": count,
        "cutoff_date": cutoff_date.strftime("%Y-%m-%d"),
    }


# =============================================================================
# TXT FILE REGENERATION
# =============================================================================


@shared_task(
    bind=True,
    name="seo.generate_txt_files",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=120,
    time_limit=300,
)
def generate_txt_files(self):
    """
    Regenerate TXT file configs that have auto_generate=True.

    For each active TXTFileConfig with auto_generate enabled, rebuilds
    the content using the appropriate generator and updates the
    last_generated timestamp.

    Note: The actual content generation logic is in the txt_files.py views.
    This task triggers a synthetic request-like generation for caching
    purposes and updates the stored content for admin visibility.

    Returns:
        dict: Summary with files_updated count and file_types list.
    """
    from apps.seo.models import TXTFileConfig

    now = timezone.now()
    updated_files = []

    configs = TXTFileConfig.objects.filter(
        is_active=True,
        auto_generate=True,
    )

    for config in configs:
        try:
            content = _generate_txt_content(config.file_type)
            if content:
                config.content = content
                config.last_generated = now
                config.save(update_fields=["content", "last_generated", "updated_at"])
                updated_files.append(config.file_type)
                logger.debug(
                    "Regenerated %s.txt content (%d chars)",
                    config.file_type,
                    len(content),
                )
        except Exception as exc:
            logger.error(
                "Failed to regenerate %s.txt: %s",
                config.file_type,
                exc,
            )

    summary = {
        "files_updated": len(updated_files),
        "file_types": updated_files,
    }
    logger.info(
        "TXT file regeneration complete: %d files updated (%s)",
        len(updated_files),
        ", ".join(updated_files) if updated_files else "none",
    )
    return summary


def _generate_txt_content(file_type: str) -> str:
    """
    Generate content for a specific TXT file type.

    Uses the same logic as the views but without requiring an HTTP request.

    Args:
        file_type: One of 'robots', 'humans', 'security', 'ads', 'llms'.

    Returns:
        Generated content string, or empty string if type is unknown.
    """
    from datetime import datetime

    host = settings.SITE_DOMAIN
    scheme = "https"

    if file_type == "robots":
        sitemap_url = f"{scheme}://{host}/sitemap.xml"
        return "\n".join(
            [
                "User-agent: *",
                "Disallow: /admin/",
                "Disallow: /api/",
                "Disallow: /media/filer/",
                "Disallow: /static/admin/",
                "",
                "User-agent: GPTBot",
                "Disallow: /",
                "",
                "User-agent: CCBot",
                "Disallow: /",
                "",
                f"Sitemap: {sitemap_url}",
            ]
        )

    elif file_type == "humans":
        now = timezone.now().strftime("%Y-%m-%d")
        return "\n".join(
            [
                "/* TEAM */",
                "Product: E-Menum - Enterprise QR Menu SaaS",
                f"Site: {scheme}://{host}",
                "Location: Istanbul, Turkey",
                "",
                "/* THANKS */",
                "Django: https://www.djangoproject.com/",
                "Tailwind CSS: https://tailwindcss.com/",
                "Alpine.js: https://alpinejs.dev/",
                "",
                "/* SITE */",
                f"Last update: {now}",
                "Language: Turkish / English",
                "Standards: HTML5, CSS3, ES6+",
                "Framework: Django 5.x",
                "Database: PostgreSQL",
                "Cache: Redis",
            ]
        )

    elif file_type == "security":
        canonical = f"{scheme}://{host}/.well-known/security.txt"
        expires = (datetime.utcnow() + timedelta(days=365)).strftime(
            "%Y-%m-%dT%H:%M:%Sz"
        )
        contact_email = settings.DEFAULT_FROM_EMAIL
        return "\n".join(
            [
                f"Contact: mailto:{contact_email}",
                f"Expires: {expires}",
                "Preferred-Languages: tr, en",
                f"Canonical: {canonical}",
                f"Policy: {scheme}://{host}/guvenlik-politikasi/",
            ]
        )

    elif file_type == "ads":
        return "\n".join(
            [
                "# ads.txt - E-Menum",
                "# No authorized digital sellers at this time.",
                "# Configure via admin -> SEO -> TXT File Configs",
            ]
        )

    elif file_type == "llms":
        return "\n".join(
            [
                "# E-Menum - Enterprise QR Menu SaaS",
                f"# {scheme}://{host}",
                "",
                "## About",
                "E-Menum is a SaaS platform providing AI-powered digital QR menus",
                "for restaurants, cafes, and food & beverage businesses in Turkey.",
                "",
                "## Usage Policy",
                "You may reference publicly available information from this site",
                "for informational purposes. Do not scrape user-generated content",
                "or private data.",
                "",
                "## Attribution",
                "When citing information from this site, please attribute to",
                f'"E-Menum ({scheme}://{host})".',
                "",
                "## Contact",
                "For questions about AI/LLM usage of our content, contact",
                f"info@{settings.SITE_DOMAIN}",
            ]
        )

    logger.warning("Unknown TXT file type: %s", file_type)
    return ""


# =============================================================================
# REDIRECT CHAIN & LOOP DETECTION
# =============================================================================


@shared_task(
    bind=True,
    name="seo.detect_redirect_chains",
    max_retries=1,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def detect_redirect_chains(self):
    """
    Detect redirect chains and loops among active Redirect rules.

    A chain is A→B→C (depth > 1). A loop is A→B→A or A→B→C→A.
    Logs warnings for chains and errors for loops.

    Returns:
        dict: Summary with chains_found and loops_found counts.
    """
    from apps.seo.models import Redirect

    redirects = {
        r.source_path: r.target_path
        for r in Redirect.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        )
    }

    chains = []
    loops = []

    for source in redirects:
        visited = [source]
        current = redirects[source]
        depth = 1

        while current in redirects and depth < 10:
            if current in visited:
                # Loop detected
                loops.append(visited + [current])
                break
            visited.append(current)
            current = redirects[current]
            depth += 1
        else:
            if depth > 1:
                # Chain (but not a loop)
                chains.append(visited + [current])

    for chain in chains:
        logger.warning(
            "Redirect chain detected (%d hops): %s",
            len(chain) - 1,
            " → ".join(chain),
        )

    for loop in loops:
        logger.error(
            "Redirect loop detected: %s",
            " → ".join(loop),
        )

    summary = {
        "total_redirects": len(redirects),
        "chains_found": len(chains),
        "loops_found": len(loops),
    }
    logger.info(
        "Redirect chain detection complete: %d redirects checked, "
        "%d chains, %d loops found",
        summary["total_redirects"],
        summary["chains_found"],
        summary["loops_found"],
    )
    return summary


# =============================================================================
# CORE WEB VITALS MEASUREMENT
# =============================================================================


@shared_task(
    bind=True,
    name="seo.measure_core_web_vitals",
    max_retries=1,
    default_retry_delay=600,
    soft_time_limit=300,
    time_limit=600,
)
def measure_core_web_vitals(self, urls=None):
    """
    Measure Core Web Vitals for key pages using Google PageSpeed Insights API.

    If no URLs are provided, measures the homepage and a set of
    representative pages.

    Args:
        urls: Optional list of URLs to measure. Defaults to key site pages.

    Returns:
        dict: Summary of measurements taken.
    """
    import requests as http_requests

    from apps.seo.models import CoreWebVitalsSnapshot

    api_key = getattr(settings, "PAGESPEED_API_KEY", "")
    site_url = getattr(settings, "SITE_URL", "https://e-menum.net")

    if not urls:
        urls = [
            site_url,
            f"{site_url}/blog/",
            f"{site_url}/fiyatlandirma/",
        ]

    results = []
    for url in urls:
        try:
            params = {
                "url": url,
                "strategy": "mobile",
                "category": "PERFORMANCE",
            }
            if api_key:
                params["key"] = api_key

            resp = http_requests.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params=params,
                timeout=60,
            )

            if resp.status_code != 200:
                logger.warning(
                    "PageSpeed API returned %d for %s: %s",
                    resp.status_code,
                    url,
                    resp.text[:200],
                )
                continue

            data = resp.json()
            lighthouse = data.get("lighthouseResult", {})
            audits = lighthouse.get("audits", {})

            # Extract CWV metrics
            lcp_val = audits.get("largest-contentful-paint", {}).get("numericValue")
            fid_val = audits.get("max-potential-fid", {}).get("numericValue")
            cls_val = audits.get("cumulative-layout-shift", {}).get("numericValue")
            ttfb_val = audits.get("server-response-time", {}).get("numericValue")
            inp_val = audits.get("interaction-to-next-paint", {}).get("numericValue")

            perf_score = None
            categories = lighthouse.get("categories", {})
            perf = categories.get("performance", {})
            if perf.get("score") is not None:
                perf_score = int(perf["score"] * 100)

            CoreWebVitalsSnapshot.objects.create(
                url=url,
                lcp=lcp_val,
                fid=fid_val,
                cls=cls_val,
                ttfb=ttfb_val,
                inp=inp_val,
                performance_score=perf_score,
                source="lighthouse",
            )
            results.append(
                {
                    "url": url,
                    "score": perf_score,
                    "lcp": lcp_val,
                    "cls": cls_val,
                }
            )
            logger.info(
                "CWV measured: url=%s score=%s lcp=%s cls=%s",
                url,
                perf_score,
                lcp_val,
                cls_val,
            )

        except http_requests.RequestException as exc:
            logger.error("CWV measurement failed for %s: %s", url, exc)
        except Exception as exc:
            logger.exception("Unexpected error measuring CWV for %s: %s", url, exc)

    summary = {
        "urls_measured": len(results),
        "urls_attempted": len(urls),
        "results": results,
    }
    logger.info(
        "Core Web Vitals measurement complete: %d/%d URLs measured",
        summary["urls_measured"],
        summary["urls_attempted"],
    )
    return summary


# =============================================================================
# INDEXNOW URL SUBMISSION
# =============================================================================


@shared_task(
    name="seo.submit_urls_to_indexnow",
    soft_time_limit=60,
    time_limit=120,
)
def submit_urls_to_indexnow(urls):
    """
    Submit a batch of URLs to IndexNow for instant indexing.

    Args:
        urls: List of full URLs to submit.

    Returns:
        dict: Submission result with success status.
    """
    from apps.seo.indexnow import IndexNowClient

    client = IndexNowClient()
    success = client.submit_urls(urls)
    return {"urls_submitted": len(urls), "success": success}
