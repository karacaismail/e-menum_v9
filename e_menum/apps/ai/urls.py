"""
URL routing for the AI application.

API Endpoints:
    POST /api/v1/ai/generate-description/  - Generate product description
    POST /api/v1/ai/improve-text/          - Improve existing text
    POST /api/v1/ai/suggest-names/         - Suggest product names
    GET  /api/v1/ai/credits/               - Check remaining credits
    GET  /api/v1/ai/history/               - Generation history
"""

from django.urls import path

from apps.ai.views import (
    CreditsView,
    GenerateDescriptionView,
    GenerationHistoryView,
    ImproveTextView,
    SuggestNamesView,
)

app_name = 'ai'

urlpatterns = [
    path('generate-description/', GenerateDescriptionView.as_view(), name='generate-description'),
    path('improve-text/', ImproveTextView.as_view(), name='improve-text'),
    path('suggest-names/', SuggestNamesView.as_view(), name='suggest-names'),
    path('credits/', CreditsView.as_view(), name='credits'),
    path('history/', GenerationHistoryView.as_view(), name='history'),
]
