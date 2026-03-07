"""
Production diagnostics endpoint.
Protected by DIAGNOSTICS_TOKEN env variable.
Access: GET /diag/?token=<DIAGNOSTICS_TOKEN>

Shows: applied/unapplied migrations, recent Django errors, DB status.
REMOVE THIS FILE AFTER DEBUGGING IS COMPLETE.
"""

import json
import logging
import os
import traceback

from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)

DIAG_TOKEN = os.environ.get("DIAGNOSTICS_TOKEN", "")


def diagnostics_view(request):
    """Secret-protected production diagnostics."""
    token = request.GET.get("token", "")

    # Require a non-empty token that matches exactly
    if not DIAG_TOKEN or token != DIAG_TOKEN:
        return HttpResponse("Not found", status=404)

    result = {
        "status": "ok",
        "migrations": {},
        "db_tables": [],
        "errors": [],
        "pricing_view_test": None,
        "order_model_test": None,
    }

    # 1. Migration status
    try:
        from django.db.migrations.executor import MigrationExecutor
        from django.db import connections

        connection = connections["default"]
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        unapplied = [f"{m[0].app_label}.{m[0].name}" for m in plan]
        result["migrations"]["unapplied"] = unapplied
        result["migrations"]["unapplied_count"] = len(unapplied)
    except Exception as e:
        result["migrations"]["error"] = str(e)
        result["errors"].append(f"Migration check: {traceback.format_exc()}")

    # 2. Check critical DB tables exist
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"
            )
            result["db_tables"] = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        result["errors"].append(f"DB table check: {str(e)}")

    # 3. Test pricing view models
    try:
        from apps.subscriptions.models import Plan, Feature

        plan_count = Plan.objects.filter(is_active=True, deleted_at__isnull=True).count()
        result["pricing_view_test"] = f"OK - {plan_count} active plans"
    except Exception as e:
        result["pricing_view_test"] = f"ERROR: {str(e)}"
        result["errors"].append(f"Pricing Plan query: {traceback.format_exc()}")

    # 4. Test order model
    try:
        from apps.orders.models import Order

        order_count = Order.objects.count()
        result["order_model_test"] = f"OK - {order_count} orders"
    except Exception as e:
        result["order_model_test"] = f"ERROR: {str(e)}"
        result["errors"].append(f"Order query: {traceback.format_exc()}")

    # 5. Test FAQ model
    try:
        from apps.website.models import FAQ

        faq_count = FAQ.objects.filter(is_active=True, page__in=["pricing", "both"]).count()
        result["faq_test"] = f"OK - {faq_count} pricing FAQs"
    except Exception as e:
        result["faq_test"] = f"ERROR: {str(e)}"
        result["errors"].append(f"FAQ query: {traceback.format_exc()}")

    # 6. Test Organization model (plan FK)
    try:
        from apps.core.models import Organization

        org_count = Organization.objects.count()
        result["org_test"] = f"OK - {org_count} orgs"
    except Exception as e:
        result["org_test"] = f"ERROR: {str(e)}"
        result["errors"].append(f"Organization query: {traceback.format_exc()}")

    # 7. Test PageHero
    try:
        from apps.website.models import PageHero

        hero = PageHero.objects.filter(page="pricing", is_active=True).first()
        result["pagehero_test"] = f"OK - hero={'yes' if hero else 'not found'}"
    except Exception as e:
        result["pagehero_test"] = f"ERROR: {str(e)}"
        result["errors"].append(f"PageHero query: {traceback.format_exc()}")

    result["status"] = "errors_found" if result["errors"] else "ok"

    return JsonResponse(result, json_dumps_params={"indent": 2})
