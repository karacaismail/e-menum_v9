"""
Django ORM models for the AI application.

Models:
- AIGeneration: Tracks every AI generation request & result
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteManager, SoftDeleteMixin, TimeStampedMixin


class GenerationType(models.TextChoices):
    """Type of AI generation performed."""
    DESCRIPTION = 'DESCRIPTION', _('Product Description')
    SHORT_DESCRIPTION = 'SHORT_DESCRIPTION', _('Short Description')
    NAME_SUGGESTION = 'NAME_SUGGESTION', _('Name Suggestion')
    SEO_TEXT = 'SEO_TEXT', _('SEO Text')
    TRANSLATION = 'TRANSLATION', _('Translation')
    IMAGE_SEARCH = 'IMAGE_SEARCH', _('Image Search')
    IMPROVE = 'IMPROVE', _('Improve Text')


class GenerationStatus(models.TextChoices):
    """Status of an AI generation request."""
    PENDING = 'PENDING', _('Pending')
    PROCESSING = 'PROCESSING', _('Processing')
    COMPLETED = 'COMPLETED', _('Completed')
    FAILED = 'FAILED', _('Failed')
    CANCELLED = 'CANCELLED', _('Cancelled')


class AIGeneration(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Tracks every AI generation request and its result.

    Each generation consumes credits from the organization's plan.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )

    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='ai_generations',
        verbose_name=_('Organization'),
    )

    user = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_generations',
        verbose_name=_('Requested by'),
    )

    # What was generated
    generation_type = models.CharField(
        max_length=30,
        choices=GenerationType.choices,
        db_index=True,
        verbose_name=_('Type'),
    )

    status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING,
        db_index=True,
        verbose_name=_('Status'),
    )

    # Input
    input_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Input text'),
        help_text=_('Original text or prompt sent to AI'),
    )

    input_context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Input context'),
        help_text=_('Additional context: product name, category, cuisine, etc.'),
    )

    # Output
    output_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Output text'),
        help_text=_('Generated text from AI'),
    )

    output_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Output data'),
        help_text=_('Structured output (alternatives, images, translations)'),
    )

    # Cost tracking
    credits_used = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Credits used'),
    )

    model_used = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('AI model'),
        help_text=_('e.g., gpt-4o-mini, claude-3-haiku'),
    )

    tokens_input = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Input tokens'),
    )

    tokens_output = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Output tokens'),
    )

    # Linked entity (optional)
    product = models.ForeignKey(
        'menu.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_generations',
        verbose_name=_('Product'),
    )

    # Error info
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Error'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'ai_generations'
        verbose_name = _('AI Generation')
        verbose_name_plural = _('AI Generations')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'generation_type'], name='aigen_org_type_idx'),
            models.Index(fields=['organization', 'status'], name='aigen_org_status_idx'),
            models.Index(fields=['product'], name='aigen_product_idx'),
        ]

    def __str__(self):
        return f"{self.get_generation_type_display()} - {self.status} ({self.organization})"


# ─────────────────────────────────────────────────────────
# AI Provider Configuration
# ─────────────────────────────────────────────────────────


class ProviderCategory(models.TextChoices):
    """Category of AI provider — text generation or image generation."""
    TEXT = 'TEXT', _('Text Generation')
    IMAGE = 'IMAGE', _('Image Generation')


class TextProvider(models.TextChoices):
    """Available text generation providers."""
    OPENAI = 'openai', _('OpenAI (GPT)')
    ANTHROPIC = 'anthropic', _('Anthropic (Claude)')
    GEMINI = 'gemini', _('Google (Gemini)')


class ImageProvider(models.TextChoices):
    """Available image generation providers."""
    OPENAI_DALLE = 'openai_dalle', _('OpenAI (DALL-E)')
    STABILITY = 'stability', _('Stability AI')
    LEONARDO = 'leonardo', _('Leonardo AI')
    MIDJOURNEY = 'midjourney', _('Midjourney')
    RUNWAY = 'runway', _('Runway')
    ADOBE_FIREFLY = 'adobe_firefly', _('Adobe Firefly')


class AIProviderConfig(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Platform-level AI provider configuration.

    Stores provider credentials and settings for superadmin management.
    No organization FK — this is a global/platform configuration.
    API keys are encrypted at rest using Django's Signer.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )

    # Provider identification
    name = models.CharField(
        max_length=100,
        verbose_name=_('Display Name'),
        help_text=_('Human-readable name (e.g., "OpenAI Production")'),
    )

    provider = models.CharField(
        max_length=50,
        verbose_name=_('Provider'),
        help_text=_('Provider identifier'),
    )

    category = models.CharField(
        max_length=10,
        choices=ProviderCategory.choices,
        db_index=True,
        verbose_name=_('Category'),
    )

    # Credentials (encrypted at rest)
    api_key_encrypted = models.TextField(
        blank=True,
        default='',
        verbose_name=_('API Key (encrypted)'),
        help_text=_('Encrypted API key stored at rest'),
    )

    # Model configuration
    default_model = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name=_('Default Model'),
        help_text=_('Default model name (e.g., gpt-4o-mini, claude-3-haiku)'),
    )

    # API endpoint override (for proxies / custom endpoints)
    api_base_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('API Base URL'),
        help_text=_('Custom API endpoint (leave blank for default)'),
    )

    # Status and priority
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Active'),
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Default Provider'),
        help_text=_('Use this provider as the default for its category'),
    )

    priority = models.PositiveIntegerField(
        default=100,
        verbose_name=_('Priority'),
        help_text=_('Lower number = higher priority for fallback'),
    )

    # Extra configuration
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Additional Settings'),
        help_text=_('Provider-specific settings (temperature, max_tokens, etc.)'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'ai_provider_configs'
        verbose_name = _('AI Provider Configuration')
        verbose_name_plural = _('AI Provider Configurations')
        ordering = ['category', 'priority', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active'], name='aiprov_cat_active_idx'),
            models.Index(fields=['provider', 'is_active'], name='aiprov_prov_active_idx'),
            models.Index(fields=['is_default', 'category'], name='aiprov_default_cat_idx'),
        ]

    def __str__(self):
        status = _('Active') if self.is_active else _('Inactive')
        return f"{self.name} ({self.get_category_display()}) - {status}"

    # ── API Key Encryption ──────────────────────────────

    def set_api_key(self, raw_key: str):
        """Encrypt and store an API key."""
        from django.core.signing import Signer
        signer = Signer(salt='ai-provider-api-key')
        self.api_key_encrypted = signer.sign(raw_key)

    def get_api_key(self) -> str:
        """Decrypt and return the API key."""
        if not self.api_key_encrypted:
            return ''
        from django.core.signing import BadSignature, Signer
        signer = Signer(salt='ai-provider-api-key')
        try:
            return signer.unsign(self.api_key_encrypted)
        except BadSignature:
            return ''

    @property
    def api_key_masked(self) -> str:
        """Return masked API key for display (last 4 chars visible)."""
        key = self.get_api_key()
        if not key:
            return ''
        if len(key) <= 8:
            return '●' * len(key)
        return '●' * (len(key) - 4) + key[-4:]

    @property
    def has_api_key(self) -> bool:
        """Check if an API key is configured."""
        return bool(self.api_key_encrypted)

    # ── Class Methods ───────────────────────────────────

    @classmethod
    def get_active_text_provider(cls):
        """Get the active default text generation provider config."""
        return cls.objects.filter(
            category=ProviderCategory.TEXT,
            is_active=True,
            is_default=True,
            deleted_at__isnull=True,
        ).first() or cls.objects.filter(
            category=ProviderCategory.TEXT,
            is_active=True,
            deleted_at__isnull=True,
        ).order_by('priority').first()

    @classmethod
    def get_active_image_provider(cls):
        """Get the active default image generation provider config."""
        return cls.objects.filter(
            category=ProviderCategory.IMAGE,
            is_active=True,
            is_default=True,
            deleted_at__isnull=True,
        ).first() or cls.objects.filter(
            category=ProviderCategory.IMAGE,
            is_active=True,
            deleted_at__isnull=True,
        ).order_by('priority').first()

    def save(self, *args, **kwargs):
        """Ensure only one default provider per category."""
        if self.is_default:
            AIProviderConfig.objects.filter(
                category=self.category,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
