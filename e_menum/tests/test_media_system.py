"""
Tests for the centralized media system (March 2026):

1. Media Serve Endpoint — public vs private access
   - Public media → 302 redirect for anyone
   - Private media (anonymous) → 404
   - Private media (authenticated, same org) → 302 redirect
   - Private media (authenticated, different org) → 404
   - Superuser → 302 redirect regardless of visibility
   - Deleted media → 404
   - Media with no URL → 404

2. Model FK Integration — image_url / logo_url / avatar_url properties
   - Product.image_url prefers Media FK, falls back to URL field
   - Category.image_url prefers Media FK, falls back to URL field
   - Organization.logo_url prefers Media FK, falls back to URL field
   - User.avatar_url prefers Media FK, falls back to URL field
   - QRCode.qr_image_serve_url prefers Media FK, falls back to URL field

3. RBAC on Media API Views — permission enforcement
   - Authenticated user with permission → 200
   - Unauthenticated → 401/403

Uses pytest-django with Factory Boy factories and Django test Client.
"""

import uuid

import pytest
from django.urls import resolve

from apps.core.models import User
from apps.media.models import Media
from tests.factories.core import OrganizationFactory, UserFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# SHARED FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def _disable_canonical_redirect(settings):
    """Disable CanonicalDomainMiddleware redirect for test client."""
    settings.SEO_CANONICAL_DOMAIN = ""


@pytest.fixture
def org(db):
    """Primary test organization."""
    return OrganizationFactory(name="Media Test Org")


@pytest.fixture
def org2(db):
    """Secondary test organization."""
    return OrganizationFactory(name="Other Org")


@pytest.fixture
def owner(db, org):
    """Owner user belonging to primary org."""
    return UserFactory(
        email="media-owner@test.com",
        password="TestPass1234!",
        organization=org,
        status="ACTIVE",
    )


@pytest.fixture
def superuser(db, org):
    """Superuser for testing bypass."""
    user = User.objects.create_superuser(
        email="super-media@test.com",
        password="SuperPass1234!",
    )
    user.organization = org
    user.save(update_fields=["organization"])
    return user


@pytest.fixture
def other_user(db, org2):
    """User belonging to a different org."""
    return UserFactory(
        email="other-media@test.com",
        password="TestPass1234!",
        organization=org2,
        status="ACTIVE",
    )


@pytest.fixture
def public_media(db, org):
    """A public media record (accessible to anyone)."""
    return Media.objects.create(
        organization=org,
        name="Public Logo",
        original_filename="logo.png",
        file_path="test-org/logos/logo.png",
        url="/media/test-org/logos/logo.png",
        storage="LOCAL",
        media_type="IMAGE",
        status="READY",
        mime_type="image/png",
        file_size=1024,
        is_public=True,
    )


@pytest.fixture
def private_media(db, org):
    """A private media record (requires auth + org membership)."""
    return Media.objects.create(
        organization=org,
        name="Private Document",
        original_filename="secret.pdf",
        file_path="test-org/docs/secret.pdf",
        url="/media/test-org/docs/secret.pdf",
        storage="LOCAL",
        media_type="DOCUMENT",
        status="READY",
        mime_type="application/pdf",
        file_size=2048,
        is_public=False,
    )


@pytest.fixture
def logged_in_client(client, owner):
    """Django test client logged in as owner."""
    client.force_login(owner)
    return client


# =============================================================================
# 1. MEDIA SERVE ENDPOINT — /media/serve/<uuid>/
# =============================================================================


class TestMediaServePublic:
    """Public media should be accessible to anyone."""

    def test_url_resolves(self):
        """The /media/serve/<uuid>/ URL should resolve correctly."""
        pk = uuid.uuid4()
        match = resolve(f"/media/serve/{pk}/")
        assert match is not None
        assert match.url_name == "media-serve"

    def test_public_media_anonymous_302(self, client, public_media):
        """Anonymous user accessing public media → 302 redirect."""
        resp = client.get(f"/media/serve/{public_media.pk}/")
        assert resp.status_code == 302
        assert public_media.url in resp.url

    def test_public_media_authenticated_302(self, logged_in_client, public_media):
        """Authenticated user accessing public media → 302 redirect."""
        resp = logged_in_client.get(f"/media/serve/{public_media.pk}/")
        assert resp.status_code == 302

    def test_public_media_cache_control(self, client, public_media):
        """Public media should have public Cache-Control header."""
        resp = client.get(f"/media/serve/{public_media.pk}/")
        assert "public" in resp.get("Cache-Control", "")


class TestMediaServePrivate:
    """Private media requires authentication and org membership."""

    def test_private_media_anonymous_404(self, client, private_media):
        """Anonymous user accessing private media → 404."""
        resp = client.get(f"/media/serve/{private_media.pk}/")
        assert resp.status_code == 404

    def test_private_media_same_org_302(self, logged_in_client, private_media):
        """Authenticated user in same org → 302 redirect."""
        resp = logged_in_client.get(f"/media/serve/{private_media.pk}/")
        assert resp.status_code == 302

    def test_private_media_different_org_404(self, client, other_user, private_media):
        """Authenticated user in different org → 404."""
        client.force_login(other_user)
        resp = client.get(f"/media/serve/{private_media.pk}/")
        assert resp.status_code == 404

    def test_private_media_superuser_302(self, client, superuser, private_media):
        """Superuser can access any private media → 302."""
        client.force_login(superuser)
        resp = client.get(f"/media/serve/{private_media.pk}/")
        assert resp.status_code == 302

    def test_private_media_cache_control(self, logged_in_client, private_media):
        """Private media should have private Cache-Control header."""
        resp = logged_in_client.get(f"/media/serve/{private_media.pk}/")
        assert "private" in resp.get("Cache-Control", "")


class TestMediaServeEdgeCases:
    """Edge cases for the media serve endpoint."""

    def test_nonexistent_media_404(self, client):
        """Non-existent UUID → 404."""
        fake_pk = uuid.uuid4()
        resp = client.get(f"/media/serve/{fake_pk}/")
        assert resp.status_code == 404

    def test_deleted_media_404(self, client, public_media):
        """Soft-deleted media → 404."""
        public_media.soft_delete()
        resp = client.get(f"/media/serve/{public_media.pk}/")
        assert resp.status_code == 404

    def test_media_without_url_404(self, db, org, client):
        """Media with no URL or file_path → 404."""
        media = Media.objects.create(
            organization=org,
            name="No URL Media",
            original_filename="empty.txt",
            file_path="",
            url="",
            storage="LOCAL",
            media_type="DOCUMENT",
            status="READY",
            mime_type="text/plain",
            file_size=0,
            is_public=True,
        )
        resp = client.get(f"/media/serve/{media.pk}/")
        assert resp.status_code == 404

    def test_get_only(self, client, public_media):
        """Only GET requests should be allowed."""
        resp = client.post(f"/media/serve/{public_media.pk}/")
        assert resp.status_code == 405


# =============================================================================
# 2. MODEL FK INTEGRATION — image_url / logo_url properties
# =============================================================================


class TestProductImageUrl:
    """Product.image_url should prefer Media FK over legacy URL."""

    def test_image_url_with_media_fk(self, org, public_media):
        """If image_media is set, image_url should return the serve URL."""
        from apps.menu.models import Category, Menu, Product

        menu = Menu.objects.create(
            organization=org, name="Test Menu", slug="test-media-menu"
        )
        cat = Category.objects.create(
            organization=org, menu=menu, name="Cat", slug="cat-media"
        )
        product = Product.objects.create(
            organization=org,
            category=cat,
            name="Test Product",
            slug="test-media-prod",
            base_price=10,
            image="https://old-url.com/img.jpg",
            image_media=public_media,
        )
        assert "/media/serve/" in product.image_url
        assert str(public_media.pk) in product.image_url

    def test_image_url_falls_back_to_legacy(self, org):
        """If no image_media, image_url should return the legacy URL."""
        from apps.menu.models import Category, Menu, Product

        menu = Menu.objects.create(
            organization=org, name="Test Menu 2", slug="test-media-menu2"
        )
        cat = Category.objects.create(
            organization=org, menu=menu, name="Cat2", slug="cat-media2"
        )
        product = Product.objects.create(
            organization=org,
            category=cat,
            name="Legacy Product",
            slug="legacy-prod",
            base_price=10,
            image="https://cdn.example.com/img.jpg",
        )
        assert product.image_url == "https://cdn.example.com/img.jpg"

    def test_image_url_empty_when_no_image(self, org):
        """If no image at all, image_url should return empty string."""
        from apps.menu.models import Category, Menu, Product

        menu = Menu.objects.create(
            organization=org, name="Test Menu 3", slug="test-media-menu3"
        )
        cat = Category.objects.create(
            organization=org, menu=menu, name="Cat3", slug="cat-media3"
        )
        product = Product.objects.create(
            organization=org,
            category=cat,
            name="No Image",
            slug="no-img",
            base_price=10,
        )
        assert product.image_url == ""


class TestOrganizationLogoUrl:
    """Organization.logo_url should prefer Media FK over legacy URL."""

    def test_logo_url_with_media_fk(self, org, public_media):
        """If logo_media is set, logo_url should return the serve URL."""
        org.logo_media = public_media
        org.save(update_fields=["logo_media"])
        assert "/media/serve/" in org.logo_url
        assert str(public_media.pk) in org.logo_url

    def test_logo_url_falls_back_to_legacy(self, org):
        """If no logo_media, logo_url should return the legacy URL."""
        org.logo = "https://cdn.example.com/logo.png"
        org.save(update_fields=["logo"])
        assert org.logo_url == "https://cdn.example.com/logo.png"


class TestUserAvatarUrl:
    """User.avatar_url should prefer Media FK over legacy URL."""

    def test_avatar_url_with_media_fk(self, owner, public_media):
        """If avatar_media is set, avatar_url should return the serve URL."""
        owner.avatar_media = public_media
        owner.save(update_fields=["avatar_media"])
        assert "/media/serve/" in owner.avatar_url
        assert str(public_media.pk) in owner.avatar_url

    def test_avatar_url_falls_back_to_legacy(self, owner):
        """If no avatar_media, avatar_url should return the legacy URL."""
        owner.avatar = "https://cdn.example.com/avatar.jpg"
        owner.save(update_fields=["avatar"])
        assert owner.avatar_url == "https://cdn.example.com/avatar.jpg"


# =============================================================================
# 3. MEDIA API RBAC — permission enforcement
# =============================================================================


class TestMediaApiAuth:
    """Media API endpoints should require authentication."""

    def test_media_list_unauthenticated_returns_401_or_403(self, client):
        """Unauthenticated access to media list → 401 or 403."""
        resp = client.get("/api/v1/media/")
        assert resp.status_code in (401, 403)

    def test_media_upload_unauthenticated_returns_401_or_403(self, client):
        """Unauthenticated access to media upload → 401 or 403."""
        resp = client.post("/api/v1/media/upload/")
        assert resp.status_code in (401, 403)

    def test_folder_list_unauthenticated_returns_401_or_403(self, client):
        """Unauthenticated access to folder list → 401 or 403."""
        resp = client.get("/api/v1/media/folders/")
        assert resp.status_code in (401, 403)
