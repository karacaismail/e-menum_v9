"""
AI Content Generation Service.

Provides text generation for product descriptions, names, SEO text,
and text improvement using OpenAI or Anthropic APIs.

Manages credit deduction from OrganizationUsage automatically.

Usage:
    from apps.ai.services import AIContentService

    service = AIContentService()
    result = service.generate_description(
        organization=org,
        user=request.user,
        product_name='Adana Kebap',
        category='Ana Yemekler',
        cuisine='Turkish',
        keywords=['spicy', 'grilled', 'traditional'],
        language='tr',
    )
    # result = {
    #     'description': 'Lezzetli Adana kebap, ...',
    #     'short_description': 'Geleneksel Adana ...',
    #     'alternatives': ['...', '...'],
    #     'credits_used': 1,
    #     'generation_id': 'uuid...',
    # }
"""

import json
import logging
from django.conf import settings
from django.utils import timezone

from apps.ai.models import AIGeneration, GenerationStatus, GenerationType
from shared.permissions.plan_enforcement import (
    FeatureNotAvailable,
    PlanEnforcementService,
    PlanLimitExceeded,
)

logger = logging.getLogger(__name__)

# Credit costs per operation
CREDIT_COSTS = {
    GenerationType.DESCRIPTION: 2,
    GenerationType.SHORT_DESCRIPTION: 1,
    GenerationType.NAME_SUGGESTION: 1,
    GenerationType.SEO_TEXT: 2,
    GenerationType.TRANSLATION: 1,
    GenerationType.IMPROVE: 1,
    GenerationType.IMAGE_SEARCH: 1,
}


class AIContentService:
    """
    Service for AI-powered content generation.

    Handles:
    1. Plan/feature check (is AI enabled for this org?)
    2. Credit check & deduction
    3. LLM API call (OpenAI / Anthropic)
    4. Logging the generation
    5. Returning structured results
    """

    def __init__(self):
        # Try database-backed configuration first
        try:
            from apps.ai.models import AIProviderConfig
            config = AIProviderConfig.get_active_text_provider()
        except Exception:
            config = None

        if config and config.has_api_key:
            self.api_key = config.get_api_key()
            self.provider = config.provider
            self.model = config.default_model or self._default_model_for_provider(config.provider)
        else:
            # Fallback to environment variables / Django settings
            self.api_key = getattr(settings, 'OPENAI_API_KEY', None) or getattr(settings, 'AI_API_KEY', '')
            self.model = getattr(settings, 'AI_MODEL', 'gpt-4o-mini')
            self.provider = getattr(settings, 'AI_PROVIDER', 'openai')

    @staticmethod
    def _default_model_for_provider(provider: str) -> str:
        """Return sensible default model name for each provider."""
        defaults = {
            'openai': 'gpt-4o-mini',
            'anthropic': 'claude-3-haiku-20240307',
            'gemini': 'gemini-1.5-flash',
        }
        return defaults.get(provider, '')

    # ─────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ─────────────────────────────────────────────────────────

    def generate_description(
        self,
        organization,
        user=None,
        product_name: str = '',
        category: str = '',
        cuisine: str = '',
        keywords: list = None,
        language: str = 'tr',
        product=None,
    ) -> dict:
        """
        Generate a product description using AI.

        Returns dict with 'description', 'short_description', 'alternatives',
        'credits_used', 'generation_id'.
        """
        self._check_feature(organization, 'ai_content_generation')
        credits_needed = CREDIT_COSTS[GenerationType.DESCRIPTION]
        self._check_credits(organization, credits_needed)

        context = {
            'product_name': product_name,
            'category': category,
            'cuisine': cuisine,
            'keywords': keywords or [],
            'language': language,
        }

        prompt = self._build_description_prompt(context)

        generation = AIGeneration.objects.create(
            organization=organization,
            user=user,
            generation_type=GenerationType.DESCRIPTION,
            status=GenerationStatus.PROCESSING,
            input_text=product_name,
            input_context=context,
            credits_used=credits_needed,
            product=product,
        )

        try:
            result = self._call_llm(prompt, max_tokens=800)

            parsed = self._parse_description_response(result['text'])

            generation.output_text = parsed.get('description', result['text'])
            generation.output_data = parsed
            generation.status = GenerationStatus.COMPLETED
            generation.model_used = result.get('model', self.model)
            generation.tokens_input = result.get('input_tokens', 0)
            generation.tokens_output = result.get('output_tokens', 0)
            generation.save()

            self._deduct_credits(organization, credits_needed)

            return {
                'description': parsed.get('description', ''),
                'short_description': parsed.get('short_description', ''),
                'alternatives': parsed.get('alternatives', []),
                'credits_used': credits_needed,
                'generation_id': str(generation.id),
            }

        except Exception as e:
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(e)
            generation.save()
            logger.error("AI generation failed: %s", e)
            raise

    def improve_text(
        self,
        organization,
        user=None,
        text: str = '',
        instruction: str = '',
        language: str = 'tr',
        product=None,
    ) -> dict:
        """
        Improve or rewrite existing text.
        """
        self._check_feature(organization, 'ai_content_generation')
        credits_needed = CREDIT_COSTS[GenerationType.IMPROVE]
        self._check_credits(organization, credits_needed)

        context = {
            'original_text': text,
            'instruction': instruction,
            'language': language,
        }

        prompt = self._build_improve_prompt(context)

        generation = AIGeneration.objects.create(
            organization=organization,
            user=user,
            generation_type=GenerationType.IMPROVE,
            status=GenerationStatus.PROCESSING,
            input_text=text,
            input_context=context,
            credits_used=credits_needed,
            product=product,
        )

        try:
            result = self._call_llm(prompt, max_tokens=600)

            generation.output_text = result['text']
            generation.status = GenerationStatus.COMPLETED
            generation.model_used = result.get('model', self.model)
            generation.tokens_input = result.get('input_tokens', 0)
            generation.tokens_output = result.get('output_tokens', 0)
            generation.save()

            self._deduct_credits(organization, credits_needed)

            return {
                'improved_text': result['text'],
                'credits_used': credits_needed,
                'generation_id': str(generation.id),
            }

        except Exception as e:
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(e)
            generation.save()
            raise

    def generate_name_suggestions(
        self,
        organization,
        user=None,
        description: str = '',
        category: str = '',
        cuisine: str = '',
        language: str = 'tr',
    ) -> dict:
        """Generate creative name suggestions for a product."""
        self._check_feature(organization, 'ai_content_generation')
        credits_needed = CREDIT_COSTS[GenerationType.NAME_SUGGESTION]
        self._check_credits(organization, credits_needed)

        context = {
            'description': description,
            'category': category,
            'cuisine': cuisine,
            'language': language,
        }

        prompt = self._build_name_suggestion_prompt(context)

        generation = AIGeneration.objects.create(
            organization=organization,
            user=user,
            generation_type=GenerationType.NAME_SUGGESTION,
            status=GenerationStatus.PROCESSING,
            input_text=description,
            input_context=context,
            credits_used=credits_needed,
        )

        try:
            result = self._call_llm(prompt, max_tokens=300)

            names = self._parse_list_response(result['text'])

            generation.output_text = result['text']
            generation.output_data = {'suggestions': names}
            generation.status = GenerationStatus.COMPLETED
            generation.model_used = result.get('model', self.model)
            generation.save()

            self._deduct_credits(organization, credits_needed)

            return {
                'suggestions': names,
                'credits_used': credits_needed,
                'generation_id': str(generation.id),
            }

        except Exception as e:
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(e)
            generation.save()
            raise

    def get_credits_remaining(self, organization) -> dict:
        """Get remaining AI credits for the organization."""
        from apps.subscriptions.models import OrganizationUsage, Feature

        plan = PlanEnforcementService.get_active_plan(organization)
        if not plan:
            return {'total': 0, 'used': 0, 'remaining': 0}

        limit = plan.get_limit('ai_credits_monthly', 0)

        try:
            feature = Feature.objects.get(code='ai_credits_monthly')
            usage = OrganizationUsage.objects.filter(
                organization=organization,
                feature=feature,
                deleted_at__isnull=True,
            ).first()
            used = usage.current_usage if usage else 0
        except (Feature.DoesNotExist, Exception):
            used = 0

        if limit == -1:
            return {'total': -1, 'used': used, 'remaining': -1}

        return {
            'total': limit,
            'used': used,
            'remaining': max(0, limit - used),
        }

    # ─────────────────────────────────────────────────────────
    # INTERNAL METHODS
    # ─────────────────────────────────────────────────────────

    def _check_feature(self, organization, feature_code: str):
        """Verify the AI feature is available on the org's plan."""
        if not PlanEnforcementService.check_feature(organization, feature_code):
            raise FeatureNotAvailable(feature_code=feature_code)

    def _check_credits(self, organization, credits_needed: int):
        """Verify org has enough AI credits remaining."""
        remaining = self.get_credits_remaining(organization)
        if remaining['remaining'] != -1 and remaining['remaining'] < credits_needed:
            raise PlanLimitExceeded(
                limit_key='ai_credits_monthly',
                current=remaining['used'],
                limit=remaining['total'],
            )

    def _deduct_credits(self, organization, credits: int):
        """Deduct AI credits from the organization's usage."""
        from apps.subscriptions.models import OrganizationUsage, Feature

        try:
            feature = Feature.objects.get(code='ai_credits_monthly')
            usage, created = OrganizationUsage.objects.get_or_create(
                organization=organization,
                feature=feature,
                defaults={
                    'current_usage': 0,
                    'usage_limit': PlanEnforcementService.get_active_plan(
                        organization
                    ).get_limit('ai_credits_monthly', 0),
                    'period_start': timezone.now(),
                    'period_end': timezone.now() + timezone.timedelta(days=30),
                }
            )
            usage.current_usage += credits
            usage.last_usage_at = timezone.now()
            usage.save(update_fields=['current_usage', 'last_usage_at', 'updated_at'])
        except Exception as e:
            logger.warning("Failed to deduct AI credits: %s", e)

    def _call_llm(self, prompt: str, max_tokens: int = 500) -> dict:
        """
        Call the LLM API (OpenAI or Anthropic).

        Falls back to a mock response if no API key is configured,
        which is useful for development/testing.
        """
        if not self.api_key:
            logger.warning("No AI API key configured — using mock response")
            return self._mock_response(prompt)

        if self.provider == 'openai':
            return self._call_openai(prompt, max_tokens)
        elif self.provider == 'anthropic':
            return self._call_anthropic(prompt, max_tokens)
        elif self.provider == 'gemini':
            return self._call_gemini(prompt, max_tokens)
        else:
            return self._mock_response(prompt)

    def _call_openai(self, prompt: str, max_tokens: int) -> dict:
        """Call OpenAI Chat Completions API."""
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': (
                            'You are a professional restaurant menu copywriter. '
                            'Write appetizing, creative descriptions in the requested language. '
                            'Be concise but evocative.'
                        ),
                    },
                    {'role': 'user', 'content': prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )

            choice = response.choices[0]
            return {
                'text': choice.message.content.strip(),
                'model': response.model,
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
            }
        except ImportError:
            logger.warning("openai package not installed, using mock")
            return self._mock_response(prompt)
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
            raise

    def _call_anthropic(self, prompt: str, max_tokens: int) -> dict:
        """Call Anthropic Messages API."""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=(
                    'You are a professional restaurant menu copywriter. '
                    'Write appetizing, creative descriptions in the requested language. '
                    'Be concise but evocative.'
                ),
                messages=[{'role': 'user', 'content': prompt}],
            )

            return {
                'text': response.content[0].text.strip(),
                'model': response.model,
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
            }
        except ImportError:
            logger.warning("anthropic package not installed, using mock")
            return self._mock_response(prompt)
        except Exception as e:
            logger.error("Anthropic API error: %s", e)
            raise

    def _call_gemini(self, prompt: str, max_tokens: int) -> dict:
        """Call Google Generative AI (Gemini) API."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                self.model,
                system_instruction=(
                    'You are a professional restaurant menu copywriter. '
                    'Write appetizing, creative descriptions in the requested language. '
                    'Be concise but evocative.'
                ),
            )

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )

            return {
                'text': response.text.strip(),
                'model': self.model,
                'input_tokens': getattr(
                    response.usage_metadata, 'prompt_token_count', 0
                ),
                'output_tokens': getattr(
                    response.usage_metadata, 'candidates_token_count', 0
                ),
            }
        except ImportError:
            logger.warning("google-generativeai package not installed, using mock")
            return self._mock_response(prompt)
        except Exception as e:
            logger.error("Gemini API error: %s", e)
            raise

    def _mock_response(self, prompt: str) -> dict:
        """
        Generate a mock response for development/testing.

        When no API key is configured, returns realistic placeholder text.
        """
        return {
            'text': json.dumps({
                'description': (
                    'Ustaca hazirlanmis, geleneksel tariflerle sunulan enfes lezzetimiz. '
                    'Taze malzemelerle ozenle hazirlanan bu ozel tarif, damaklarda '
                    'unutulmaz bir tat birakiyor. Sizi misafirlerimiz olarak agirlamaktan '
                    'mutluluk duyariz.'
                ),
                'short_description': 'Geleneksel tarifle hazirlanan ozel lezzetimiz.',
                'alternatives': [
                    'Sef\'imizin ozenle hazirladi enfes lezzet.',
                    'Taze malzemelerle ustaca pisirilmis bir basit.',
                ],
            }),
            'model': 'mock-dev',
            'input_tokens': 0,
            'output_tokens': 0,
        }

    # ─────────────────────────────────────────────────────────
    # PROMPT BUILDERS
    # ─────────────────────────────────────────────────────────

    def _build_description_prompt(self, context: dict) -> str:
        lang = context.get('language', 'tr')
        lang_name = 'Turkish' if lang == 'tr' else 'English'
        keywords = ', '.join(context.get('keywords', []))

        return (
            f"Generate a menu item description in {lang_name}.\n\n"
            f"Product Name: {context.get('product_name', '')}\n"
            f"Category: {context.get('category', '')}\n"
            f"Cuisine: {context.get('cuisine', '')}\n"
            f"Keywords: {keywords}\n\n"
            f"Return ONLY a JSON object with these keys:\n"
            f"- \"description\": A detailed appetizing description (2-3 sentences)\n"
            f"- \"short_description\": A brief one-line tagline\n"
            f"- \"alternatives\": An array of 2 alternative short descriptions\n\n"
            f"Output valid JSON only, no markdown."
        )

    def _build_improve_prompt(self, context: dict) -> str:
        lang = context.get('language', 'tr')
        lang_name = 'Turkish' if lang == 'tr' else 'English'
        instruction = context.get('instruction', 'Make it more appetizing and professional.')

        return (
            f"Improve the following restaurant menu text in {lang_name}.\n\n"
            f"Original text: {context.get('original_text', '')}\n"
            f"Instruction: {instruction}\n\n"
            f"Return ONLY the improved text, nothing else."
        )

    def _build_name_suggestion_prompt(self, context: dict) -> str:
        lang = context.get('language', 'tr')
        lang_name = 'Turkish' if lang == 'tr' else 'English'

        return (
            f"Suggest 5 creative menu item names in {lang_name}.\n\n"
            f"Description: {context.get('description', '')}\n"
            f"Category: {context.get('category', '')}\n"
            f"Cuisine: {context.get('cuisine', '')}\n\n"
            f"Return ONLY a JSON array of 5 name strings.\n"
            f"Example: [\"Name 1\", \"Name 2\", \"Name 3\", \"Name 4\", \"Name 5\"]"
        )

    # ─────────────────────────────────────────────────────────
    # RESPONSE PARSERS
    # ─────────────────────────────────────────────────────────

    def _parse_description_response(self, text: str) -> dict:
        """Parse JSON description response from LLM."""
        try:
            # Try to parse as JSON
            cleaned = text.strip()
            if cleaned.startswith('```'):
                # Strip markdown code blocks
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
            data = json.loads(cleaned)
            return {
                'description': data.get('description', ''),
                'short_description': data.get('short_description', ''),
                'alternatives': data.get('alternatives', []),
            }
        except (json.JSONDecodeError, ValueError):
            # If not JSON, treat the whole text as description
            return {
                'description': text.strip(),
                'short_description': text.strip()[:100],
                'alternatives': [],
            }

    def _parse_list_response(self, text: str) -> list:
        """Parse JSON array response from LLM."""
        try:
            cleaned = text.strip()
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
            return [text.strip()]
        except (json.JSONDecodeError, ValueError):
            # Split by newlines as fallback
            return [line.strip('- ').strip() for line in text.strip().split('\n') if line.strip()]
