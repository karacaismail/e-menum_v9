"""
DRF Serializers for the AI application.

Extracted from views.py for separation of concerns and reusability.
"""

from rest_framework import serializers


class GenerateDescriptionSerializer(serializers.Serializer):
    """Serializer for AI description generation requests."""
    product_name = serializers.CharField(
        max_length=200,
        help_text='Urun adi (orn: "Karisik Izgara")',
    )
    category = serializers.CharField(
        max_length=100,
        required=False,
        default='',
        help_text='Urun kategorisi (orn: "Ana Yemekler")',
    )
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        help_text='Anahtar kelimeler (orn: ["baharatli", "firinda"])',
    )
    language = serializers.ChoiceField(
        choices=[('tr', 'Turkce'), ('en', 'English'), ('ar', 'Arabic'), ('ru', 'Russian'), ('de', 'Deutsch')],
        default='tr',
    )
    tone = serializers.ChoiceField(
        choices=[
            ('professional', 'Profesyonel'),
            ('casual', 'Samimi'),
            ('luxury', 'Premium'),
            ('fun', 'Eglenceli'),
        ],
        default='professional',
    )
    max_length = serializers.IntegerField(
        min_value=50,
        max_value=500,
        default=200,
        help_text='Maksimum karakter sayisi',
    )


class ImproveTextSerializer(serializers.Serializer):
    """Serializer for AI text improvement requests."""
    text = serializers.CharField(
        max_length=2000,
        help_text='Iyilestirilecek metin',
    )
    improvement_type = serializers.ChoiceField(
        choices=[
            ('grammar', 'Gramer duzeltme'),
            ('style', 'Stil iyilestirme'),
            ('seo', 'SEO optimizasyonu'),
            ('shorten', 'Kisaltma'),
            ('expand', 'Genisletme'),
        ],
        default='style',
    )
    language = serializers.ChoiceField(
        choices=[('tr', 'Turkce'), ('en', 'English')],
        default='tr',
    )


class SuggestNamesSerializer(serializers.Serializer):
    """Serializer for AI name suggestion requests."""
    description = serializers.CharField(
        max_length=500,
        help_text='Urun/kategori aciklamasi',
    )
    category = serializers.CharField(
        max_length=100,
        required=False,
        default='',
    )
    count = serializers.IntegerField(
        min_value=1,
        max_value=10,
        default=5,
        help_text='Kac adet oneri uretilsin',
    )
    language = serializers.ChoiceField(
        choices=[('tr', 'Turkce'), ('en', 'English')],
        default='tr',
    )


class AIGenerationSerializer(serializers.Serializer):
    """Read-only serializer for AI generation history."""
    id = serializers.UUIDField(read_only=True)
    generation_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    input_text = serializers.CharField(read_only=True)
    output_text = serializers.CharField(read_only=True)
    credits_used = serializers.IntegerField(read_only=True)
    model_used = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class AICreditsSerializer(serializers.Serializer):
    """Serializer for AI credits response."""
    total_credits = serializers.IntegerField()
    used_credits = serializers.IntegerField()
    remaining_credits = serializers.IntegerField()
    plan_name = serializers.CharField()
