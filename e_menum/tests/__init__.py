"""
E-Menum Django Test Suite

This package contains all tests for the E-Menum Django application.

Test Organization:
- tests/core/          - Core app tests (User, Organization, Role, etc.)
- tests/menu/          - Menu module tests
- tests/orders/        - Orders module tests
- tests/subscriptions/ - Subscription module tests
- tests/customers/     - Customer module tests
- tests/api/           - API integration tests
- tests/shared/        - Shared utility tests

Running Tests:
    # Run all tests
    pytest

    # Run with coverage
    pytest --cov=apps --cov-report=term-missing

    # Run specific test file
    pytest tests/core/test_models.py

    # Run specific test
    pytest tests/core/test_models.py::TestOrganization::test_create_organization

    # Run tests by marker
    pytest -m unit        # Unit tests only
    pytest -m integration # Integration tests only
    pytest -m api         # API tests only

Test Markers:
    @pytest.mark.unit         - Isolated unit tests
    @pytest.mark.integration  - Tests with database/external services
    @pytest.mark.e2e          - End-to-end tests
    @pytest.mark.slow         - Long-running tests
    @pytest.mark.api          - API endpoint tests
    @pytest.mark.model        - Model tests
"""
