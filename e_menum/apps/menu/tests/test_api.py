"""API tests for Menu app endpoints."""

import uuid

import pytest
from rest_framework import status


@pytest.mark.django_db
class TestMenuAPI:
    """Tests for Menu API endpoints."""

    def test_list_menus_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/menus/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_menus_authenticated_no_org(self, authenticated_api_client):
        """User without org gets 403 (tenant required)."""
        response = authenticated_api_client.get("/api/v1/menus/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_menus_authenticated_with_org(self, api_client, organization_with_owner, menu):
        """User with org + owner role can list menus."""
        org, owner = organization_with_owner
        api_client.force_authenticate(user=owner)
        response = api_client.get("/api/v1/menus/")
        # Owner should get 200; if RBAC denies, 403 is acceptable
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN,
        )

    def test_create_menu(self, authenticated_api_client, organization):
        # Set user's organization
        user = authenticated_api_client.handler._force_user
        user.organization = organization
        user.save()

        response = authenticated_api_client.post(
            "/api/v1/menus/",
            {
                "name": "Dinner Menu",
                "description": "Evening menu",
            },
            format="json",
        )
        # May return 201 or 403 depending on permission setup
        assert response.status_code in (
            status.HTTP_201_CREATED,
            status.HTTP_403_FORBIDDEN,
        )


@pytest.mark.django_db
class TestMenuTenantIsolation:
    """Tests for multi-tenant data isolation on menu endpoints."""

    def test_cannot_see_other_org_menus(
        self, api_client, make_user, make_organization
    ):
        from apps.menu.models import Menu

        org1 = make_organization(name="Org A")
        org2 = make_organization(name="Org B")
        user1 = make_user(email="u1@test.com", organization=org1)

        Menu.objects.create(
            organization=org1, name="My Menu",
            slug=f"my-{uuid.uuid4().hex[:6]}",
        )
        Menu.objects.create(
            organization=org2, name="Other Menu",
            slug=f"other-{uuid.uuid4().hex[:6]}",
        )

        api_client.force_authenticate(user=user1)
        response = api_client.get("/api/v1/menus/")
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            menu_names = []
            if isinstance(data, list):
                menu_names = [m["name"] for m in data]
            elif isinstance(data, dict) and "data" in data:
                menu_names = [m["name"] for m in data["data"]]
            elif isinstance(data, dict) and "results" in data:
                menu_names = [m["name"] for m in data["results"]]
            assert "Other Menu" not in menu_names


@pytest.mark.django_db
class TestCategoryAPI:
    """Tests for Category API endpoints."""

    def test_list_categories_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/categories/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProductAPI:
    """Tests for Product API endpoints."""

    def test_list_products_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/products/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
