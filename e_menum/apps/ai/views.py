"""
API Views for the AI application.

Provides endpoints for AI content generation:
- POST /api/v1/ai/generate-description/  - Generate product description
- POST /api/v1/ai/improve-text/          - Improve existing text
- POST /api/v1/ai/suggest-names/         - Suggest product names
- GET  /api/v1/ai/credits/               - Check remaining credits
- GET  /api/v1/ai/history/               - Generation history
"""

import logging

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.models import AIGeneration
from apps.ai.services import AIContentService
from shared.permissions.plan_enforcement import (
    FeatureNotAvailable,
    PlanLimitExceeded,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# REQUEST SERIALIZERS
# ─────────────────────────────────────────────────────────────


class GenerateDescriptionSerializer(serializers.Serializer):
    product_name = serializers.CharField(max_length=200)
    category = serializers.CharField(max_length=100, required=False, default="")
    cuisine = serializers.CharField(max_length=100, required=False, default="")
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
    )
    language = serializers.ChoiceField(
        choices=[("tr", "Turkish"), ("en", "English")], default="tr"
    )
    product_id = serializers.UUIDField(required=False, allow_null=True)


class ImproveTextSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000)
    instruction = serializers.CharField(max_length=500, required=False, default="")
    language = serializers.ChoiceField(
        choices=[("tr", "Turkish"), ("en", "English")], default="tr"
    )
    product_id = serializers.UUIDField(required=False, allow_null=True)


class SuggestNamesSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=1000, required=False, default="")
    category = serializers.CharField(max_length=100, required=False, default="")
    cuisine = serializers.CharField(max_length=100, required=False, default="")
    language = serializers.ChoiceField(
        choices=[("tr", "Turkish"), ("en", "English")], default="tr"
    )


# ─────────────────────────────────────────────────────────────
# VIEWS
# ─────────────────────────────────────────────────────────────


class GenerateDescriptionView(APIView):
    """POST /api/v1/ai/generate-description/ — Generate product description."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateDescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization = getattr(request, "organization", None)
        if not organization:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_ORGANIZATION",
                        "message": "No organization context",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Resolve product if provided
        product = None
        if data.get("product_id"):
            from apps.menu.models import Product

            product = Product.objects.filter(
                id=data["product_id"],
                category__menu__organization=organization,
                deleted_at__isnull=True,
            ).first()

        try:
            service = AIContentService()
            result = service.generate_description(
                organization=organization,
                user=request.user,
                product_name=data["product_name"],
                category=data["category"],
                cuisine=data["cuisine"],
                keywords=data["keywords"],
                language=data["language"],
                product=product,
            )
            return Response({"success": True, "data": result})

        except FeatureNotAvailable as e:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "FEATURE_NOT_AVAILABLE",
                        "message": str(e.detail),
                    },
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except PlanLimitExceeded as e:
            return Response(
                {
                    "success": False,
                    "error": {"code": "CREDITS_EXHAUSTED", "message": str(e.detail)},
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            logger.error("AI generation error: %s", e)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "AI_ERROR",
                        "message": "AI generation failed. Please try again.",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImproveTextView(APIView):
    """POST /api/v1/ai/improve-text/ — Improve existing text."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ImproveTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization = getattr(request, "organization", None)
        if not organization:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_ORGANIZATION",
                        "message": "No organization context",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = None
        if data.get("product_id"):
            from apps.menu.models import Product

            product = Product.objects.filter(
                id=data["product_id"],
                category__menu__organization=organization,
                deleted_at__isnull=True,
            ).first()

        try:
            service = AIContentService()
            result = service.improve_text(
                organization=organization,
                user=request.user,
                text=data["text"],
                instruction=data["instruction"],
                language=data["language"],
                product=product,
            )
            return Response({"success": True, "data": result})

        except (FeatureNotAvailable, PlanLimitExceeded) as e:
            return Response(
                {
                    "success": False,
                    "error": {"code": "PLAN_LIMIT", "message": str(e.detail)},
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            logger.error("AI improve error: %s", e)
            return Response(
                {
                    "success": False,
                    "error": {"code": "AI_ERROR", "message": "AI improvement failed."},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SuggestNamesView(APIView):
    """POST /api/v1/ai/suggest-names/ — Suggest product names."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SuggestNamesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization = getattr(request, "organization", None)
        if not organization:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_ORGANIZATION",
                        "message": "No organization context",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = AIContentService()
            result = service.generate_name_suggestions(
                organization=organization,
                user=request.user,
                description=data["description"],
                category=data["category"],
                cuisine=data["cuisine"],
                language=data["language"],
            )
            return Response({"success": True, "data": result})

        except (FeatureNotAvailable, PlanLimitExceeded) as e:
            return Response(
                {
                    "success": False,
                    "error": {"code": "PLAN_LIMIT", "message": str(e.detail)},
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            logger.error("AI suggest error: %s", e)
            return Response(
                {
                    "success": False,
                    "error": {"code": "AI_ERROR", "message": "Name suggestion failed."},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreditsView(APIView):
    """GET /api/v1/ai/credits/ — Check remaining AI credits."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = getattr(request, "organization", None)
        if not organization:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_ORGANIZATION",
                        "message": "No organization context",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = AIContentService()
        credits = service.get_credits_remaining(organization)
        return Response({"success": True, "data": credits})


class GenerationHistoryView(APIView):
    """GET /api/v1/ai/history/ — List AI generation history for org."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = getattr(request, "organization", None)
        if not organization:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_ORGANIZATION",
                        "message": "No organization context",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = AIGeneration.objects.filter(
            organization=organization,
            deleted_at__isnull=True,
        ).order_by("-created_at")[:50]

        data = [
            {
                "id": str(g.id),
                "type": g.generation_type,
                "status": g.status,
                "input_text": g.input_text[:100] if g.input_text else "",
                "output_text": g.output_text[:200] if g.output_text else "",
                "credits_used": g.credits_used,
                "model": g.model_used or "",
                "created_at": g.created_at.isoformat(),
            }
            for g in qs
        ]

        return Response({"success": True, "data": data})
