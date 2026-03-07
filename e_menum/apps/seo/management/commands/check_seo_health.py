"""
Management command to check SEO health across the site.

Reports on:
- BlogPost SEO scores and missing metadata
- Redirect status (active/inactive)
- Broken link counts (resolved/unresolved)
- pSEO page counts (published/draft)

Usage:
    python manage.py check_seo_health
"""

import logging

from django.core.management.base import BaseCommand
from django.db.models import Avg, Q

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check SEO health across the site and print a formatted report'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=========================================='
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '  SEO Health Report'
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '==========================================\n'
        ))

        self._check_blog_posts()
        self._check_redirects()
        self._check_broken_links()
        self._check_pseo_pages()

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=========================================='
        ))
        self.stdout.write(self.style.SUCCESS(
            '  Report complete.'
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '==========================================\n'
        ))

    # ──────────────────────────────────────────────────────────────
    # Blog Posts
    # ──────────────────────────────────────────────────────────────

    def _check_blog_posts(self):
        self.stdout.write(self.style.HTTP_INFO('--- Blog Posts ---'))

        try:
            from apps.website.models import BlogPost
        except ImportError:
            self.stdout.write(self.style.WARNING(
                '  BlogPost model not available, skipping.'
            ))
            return

        total = BlogPost.objects.count()
        if total == 0:
            self.stdout.write('  No blog posts found.')
            self.stdout.write('')
            return

        # Average SEO score
        avg_score = BlogPost.objects.aggregate(
            avg=Avg('seo_score')
        )['avg'] or 0

        self.stdout.write(f'  Total blog posts: {total}')
        self.stdout.write(f'  Average SEO score: {avg_score:.1f}/100')

        # Posts with zero score
        zero_score = BlogPost.objects.filter(seo_score=0).count()
        if zero_score > 0:
            self.stdout.write(self.style.WARNING(
                f'  Posts with SEO score = 0: {zero_score}'
            ))

        # Posts with empty meta_title
        empty_title = BlogPost.objects.filter(
            Q(meta_title='') | Q(meta_title__isnull=True)
        ).count()
        if empty_title > 0:
            self.stdout.write(self.style.WARNING(
                f'  Posts with empty meta_title: {empty_title}'
            ))

        # Posts with empty meta_description
        empty_desc = BlogPost.objects.filter(
            Q(meta_description='') | Q(meta_description__isnull=True)
        ).count()
        if empty_desc > 0:
            self.stdout.write(self.style.WARNING(
                f'  Posts with empty meta_description: {empty_desc}'
            ))

        # List the problematic posts
        problem_posts = BlogPost.objects.filter(
            Q(seo_score=0) | Q(meta_title='') | Q(meta_title__isnull=True)
        ).values_list('title', 'seo_score')[:10]

        if problem_posts:
            self.stdout.write('')
            self.stdout.write('  Posts needing attention:')
            for title, score in problem_posts:
                truncated = title[:50] + '...' if len(title) > 50 else title
                self.stdout.write(
                    f'    - "{truncated}" (score: {score})'
                )

        self.stdout.write('')

    # ──────────────────────────────────────────────────────────────
    # Redirects
    # ──────────────────────────────────────────────────────────────

    def _check_redirects(self):
        self.stdout.write(self.style.HTTP_INFO('--- Redirects ---'))

        from apps.seo.models import Redirect

        total = Redirect.objects.count()
        active = Redirect.objects.filter(is_active=True).count()
        inactive = total - active

        self.stdout.write(f'  Total redirects: {total}')
        self.stdout.write(f'  Active: {active}')
        self.stdout.write(f'  Inactive: {inactive}')

        # Top redirects by hit count
        top_redirects = Redirect.objects.filter(
            is_active=True, hit_count__gt=0
        ).order_by('-hit_count')[:5]

        if top_redirects:
            self.stdout.write('')
            self.stdout.write('  Most-hit redirects:')
            for r in top_redirects:
                self.stdout.write(
                    f'    - {r.source_path} -> {r.target_path} '
                    f'({r.hit_count} hits)'
                )

        self.stdout.write('')

    # ──────────────────────────────────────────────────────────────
    # Broken Links
    # ──────────────────────────────────────────────────────────────

    def _check_broken_links(self):
        self.stdout.write(self.style.HTTP_INFO('--- Broken Links ---'))

        from apps.seo.models import BrokenLink

        total = BrokenLink.objects.count()
        resolved = BrokenLink.objects.filter(is_resolved=True).count()
        unresolved = total - resolved

        self.stdout.write(f'  Total broken links: {total}')
        self.stdout.write(f'  Resolved: {resolved}')

        if unresolved > 0:
            self.stdout.write(self.style.WARNING(
                f'  Unresolved: {unresolved}'
            ))

            # Show top unresolved by check count
            top_unresolved = BrokenLink.objects.filter(
                is_resolved=False
            ).order_by('-check_count')[:5]

            if top_unresolved:
                self.stdout.write('')
                self.stdout.write('  Top unresolved broken links:')
                for bl in top_unresolved:
                    self.stdout.write(
                        f'    - {bl.target_url} '
                        f'(status: {bl.status_code}, '
                        f'checked {bl.check_count}x)'
                    )
        else:
            self.stdout.write(self.style.SUCCESS(
                '  Unresolved: 0 (all clear!)'
            ))

        self.stdout.write('')

    # ──────────────────────────────────────────────────────────────
    # pSEO Pages
    # ──────────────────────────────────────────────────────────────

    def _check_pseo_pages(self):
        self.stdout.write(self.style.HTTP_INFO('--- pSEO Pages ---'))

        from apps.seo.models import PSEOPage

        total = PSEOPage.objects.count()
        published = PSEOPage.objects.filter(is_published=True).count()
        draft = total - published

        self.stdout.write(f'  Total pSEO pages: {total}')
        self.stdout.write(f'  Published: {published}')
        self.stdout.write(f'  Draft: {draft}')

        if total > 0:
            # Average quality score
            avg_quality = PSEOPage.objects.aggregate(
                avg=Avg('quality_score')
            )['avg'] or 0
            self.stdout.write(f'  Average quality score: {avg_quality:.1f}/100')

            # Low quality pages
            low_quality = PSEOPage.objects.filter(
                quality_score__lt=50
            ).count()
            if low_quality > 0:
                self.stdout.write(self.style.WARNING(
                    f'  Low quality (score < 50): {low_quality}'
                ))

        self.stdout.write('')
