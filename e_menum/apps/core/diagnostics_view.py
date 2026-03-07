"""
Production diagnostics endpoint.
Protected by DIAGNOSTICS_TOKEN env variable (default: emenum-debug-2026).
Access: GET /diag/?token=<DIAGNOSTICS_TOKEN>

Tests key model queries that could cause 500 errors on pricing/orders pages.
REMOVE THIS FILE AFTER DEBUGGING IS COMPLETE.
"""

import logging
import os
import traceback

from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)

DIAG_TOKEN = os.environ.get("DIAGNOSTICS_TOKEN", "emenum-debug-2026")


def diagnostics_view(request):
    """Secret-protected production diagnostics."""
    token = request.GET.get("token", "")
    if not DIAG_TOKEN or token != DIAG_TOKEN:
        return HttpResponse("Not found", status=404)

    errors = []
    result = {
        "status": "ok",
        "migrations": {},
        "db_tables": [],
        "errors": errors,
        "tests": {},
    }

    # 1. Migration status
    try:
        from django.db import connections
        from django.db.migrations.executor import MigrationExecutor

        connection = connections["default"]
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        unapplied = [f"{m[0].app_label}.{m[0].name}" for m in plan]
        result["migrations"]["unapplied"] = unapplied
        result["migrations"]["unapplied_count"] = len(unapplied)
    except Exception:
        result["migrations"]["error"] = traceback.format_exc()
        errors.append("Migration check failed")

    # 2. List DB tables
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables"
                " WHERE table_schema='public' ORDER BY table_name;"
            )
            result["db_tables"] = [row[0] for row in cursor.fetchall()]
    except Exception:
        errors.append(f"DB table check failed: {traceback.format_exc()}")

    # 3. Test pricing models (Plan query)
    try:
        from apps.subscriptions.models import Plan

        count = Plan.objects.filter(is_active=True, deleted_at__isnull=True).count()
        result["tests"]["plan"] = f"OK - {count} active plans"
    except Exception:
        result["tests"]["plan"] = f"ERROR: {traceback.format_exc()}"
        errors.append("Plan query failed")

    # 4. Test Order model
    try:
        from apps.orders.models import Order

        count = Order.objects.count()
        result["tests"]["order"] = f"OK - {count} orders"
    except Exception:
        result["tests"]["order"] = f"ERROR: {traceback.format_exc()}"
        errors.append("Order query failed")

    # 5. Test FAQ model
    try:
        from apps.website.models import FAQ

        count = FAQ.objects.filter(is_active=True, page__in=["pricing", "both"]).count()
        result["tests"]["faq"] = f"OK - {count} pricing FAQs"
    except Exception:
        result["tests"]["faq"] = f"ERROR: {traceback.format_exc()}"
        errors.append("FAQ query failed")

    # 6. Test Organization model (plan FK)
    try:
        from apps.core.models import Organization

        count = Organization.objects.count()
        result["tests"]["organization"] = f"OK - {count} orgs"
    except Exception:
        result["tests"]["organization"] = f"ERROR: {traceback.format_exc()}"
        errors.append("Organization query failed")

    # 7. Test PageHero model
    try:
        from apps.website.models import PageHero

        hero = PageHero.objects.filter(page="pricing", is_active=True).first()
        result["tests"]["pagehero"] = f"OK - hero={'found' if hero else 'not found'}"
    except Exception:
        result["tests"]["pagehero"] = f"ERROR: {traceback.format_exc()}"
        errors.append("PageHero query failed")

    result["status"] = "errors_found" if errors else "ok"

    # 8. Directly call PricingView and render to string to catch real 500 cause
    try:
        from django.template.loader import render_to_string
        from django.test import RequestFactory

        from apps.website.views.pricing import PricingView

        factory = RequestFactory()
        req = factory.get("/tr/fiyatlandirma/")
        req.LANGUAGE_CODE = "tr"

        # Get context
        view = PricingView()
        view.request = req
        view.args = []
        view.kwargs = {}
        ctx = view.get_context_data()

        # Render template
        html = render_to_string("website/pricing.html", ctx, request=req)
        result["pricing_render"] = {
            "ok": True,
            "html_length": len(html),
        }
    except Exception:
        result["pricing_render"] = {
            "ok": False,
            "traceback": traceback.format_exc(),
        }

    return JsonResponse(result, json_dumps_params={"indent": 2})
