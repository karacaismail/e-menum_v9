"""
Tests for apps.seo.tasks.detect_redirect_chains.

Covers:
- No redirects returns 0 chains, 0 loops
- A->B (single redirect, depth 1) returns 0 chains, 0 loops
- A->B->C (chain, depth 2) returns 1 chain, 0 loops
- A->B->A (loop, depth 2) returns 0 chains, 1 loop
- A->B->C->A (longer loop, depth 3) returns 0 chains, 1 loop
"""

from django.test import TestCase

from apps.seo.models import Redirect
from apps.seo.tasks import detect_redirect_chains


class TestDetectRedirectChainsEmpty(TestCase):
    """Test chain detection with no redirects."""

    def test_no_redirects_returns_zero_chains_and_loops(self):
        """With no redirect rules, the result should have 0 chains and 0 loops."""
        result = detect_redirect_chains()

        self.assertEqual(result["chains_found"], 0)
        self.assertEqual(result["loops_found"], 0)
        self.assertEqual(result["total_redirects"], 0)


class TestDetectRedirectChainsSingleRedirect(TestCase):
    """Test chain detection with a single A->B redirect."""

    def test_single_redirect_no_chain_no_loop(self):
        """A single A->B redirect (depth 1) should not be flagged as a chain or loop."""
        Redirect.objects.create(
            source_path="/page-a/",
            target_path="/page-b/",
            is_active=True,
        )

        result = detect_redirect_chains()

        self.assertEqual(result["total_redirects"], 1)
        self.assertEqual(result["chains_found"], 0)
        self.assertEqual(result["loops_found"], 0)


class TestDetectRedirectChainsDetection(TestCase):
    """Test chain detection with A->B->C (chain, depth 2)."""

    def test_a_to_b_to_c_detected_as_chain(self):
        """A->B->C (depth > 1) should be detected as 1 chain, 0 loops."""
        Redirect.objects.create(
            source_path="/a/",
            target_path="/b/",
            is_active=True,
        )
        Redirect.objects.create(
            source_path="/b/",
            target_path="/c/",
            is_active=True,
        )

        result = detect_redirect_chains()

        self.assertEqual(result["total_redirects"], 2)
        self.assertEqual(result["chains_found"], 1)
        self.assertEqual(result["loops_found"], 0)

    def test_a_to_b_to_c_to_d_detected_as_chain(self):
        """A->B->C->D (depth 3) should be detected as a chain. B->C->D is also a chain."""
        Redirect.objects.create(
            source_path="/x/",
            target_path="/y/",
            is_active=True,
        )
        Redirect.objects.create(
            source_path="/y/",
            target_path="/z/",
            is_active=True,
        )
        Redirect.objects.create(
            source_path="/z/",
            target_path="/w/",
            is_active=True,
        )

        result = detect_redirect_chains()

        self.assertEqual(result["total_redirects"], 3)
        # /x/ -> /y/ -> /z/ -> /w/ is a chain (depth 3)
        # /y/ -> /z/ -> /w/ is also a chain (depth 2)
        # /z/ -> /w/ is just a single redirect (depth 1), not a chain
        self.assertEqual(result["chains_found"], 2)
        self.assertEqual(result["loops_found"], 0)


class TestDetectRedirectLoopsShort(TestCase):
    """Test loop detection with A->B->A (short loop)."""

    def test_a_to_b_to_a_detected_as_loop(self):
        """A->B->A should be detected as 1 loop, 0 chains."""
        Redirect.objects.create(
            source_path="/loop-a/",
            target_path="/loop-b/",
            is_active=True,
        )
        Redirect.objects.create(
            source_path="/loop-b/",
            target_path="/loop-a/",
            is_active=True,
        )

        result = detect_redirect_chains()

        self.assertEqual(result["total_redirects"], 2)
        self.assertEqual(result["chains_found"], 0)
        # Both /loop-a/ and /loop-b/ detect the same logical loop,
        # but each starting point generates a separate loop entry.
        self.assertEqual(result["loops_found"], 2)


class TestDetectRedirectLoopsLonger(TestCase):
    """Test loop detection with A->B->C->A (longer loop)."""

    def test_a_to_b_to_c_to_a_detected_as_loop(self):
        """A->B->C->A should be detected as a loop, with no chains."""
        Redirect.objects.create(
            source_path="/tri-a/",
            target_path="/tri-b/",
            is_active=True,
        )
        Redirect.objects.create(
            source_path="/tri-b/",
            target_path="/tri-c/",
            is_active=True,
        )
        Redirect.objects.create(
            source_path="/tri-c/",
            target_path="/tri-a/",
            is_active=True,
        )

        result = detect_redirect_chains()

        self.assertEqual(result["total_redirects"], 3)
        self.assertEqual(result["chains_found"], 0)
        # All three starting points lead to the same cyclic loop
        self.assertEqual(result["loops_found"], 3)


class TestDetectRedirectChainsInactiveIgnored(TestCase):
    """Test that inactive and soft-deleted redirects are ignored."""

    def test_inactive_redirects_are_excluded(self):
        """Inactive redirects should not be considered for chain detection."""
        Redirect.objects.create(
            source_path="/inactive-a/",
            target_path="/inactive-b/",
            is_active=False,
        )
        Redirect.objects.create(
            source_path="/inactive-b/",
            target_path="/inactive-c/",
            is_active=True,
        )

        result = detect_redirect_chains()

        # Only 1 active redirect; no chain since /inactive-a/ is inactive
        self.assertEqual(result["total_redirects"], 1)
        self.assertEqual(result["chains_found"], 0)
        self.assertEqual(result["loops_found"], 0)

    def test_soft_deleted_redirects_are_excluded(self):
        """Soft-deleted redirects should not be considered."""
        from django.utils import timezone

        Redirect.all_objects.create(
            source_path="/deleted-a/",
            target_path="/deleted-b/",
            is_active=True,
            deleted_at=timezone.now(),
        )
        Redirect.objects.create(
            source_path="/deleted-b/",
            target_path="/deleted-c/",
            is_active=True,
        )

        result = detect_redirect_chains()

        # Only /deleted-b/ -> /deleted-c/ is active and not deleted
        self.assertEqual(result["total_redirects"], 1)
        self.assertEqual(result["chains_found"], 0)
        self.assertEqual(result["loops_found"], 0)


class TestDetectRedirectChainsMixed(TestCase):
    """Test with a mix of chains, loops, and standalone redirects."""

    def test_mixed_chains_and_standalone(self):
        """A mix of chain and standalone redirects should be counted correctly."""
        # Standalone: /s1/ -> /s2/ (no chain)
        Redirect.objects.create(
            source_path="/s1/",
            target_path="/s2/",
            is_active=True,
        )
        # Chain: /c1/ -> /c2/ -> /c3/
        Redirect.objects.create(
            source_path="/c1/",
            target_path="/c2/",
            is_active=True,
        )
        Redirect.objects.create(
            source_path="/c2/",
            target_path="/c3/",
            is_active=True,
        )

        result = detect_redirect_chains()

        self.assertEqual(result["total_redirects"], 3)
        # /c1/ -> /c2/ -> /c3/ is a chain (depth 2)
        self.assertEqual(result["chains_found"], 1)
        self.assertEqual(result["loops_found"], 0)
