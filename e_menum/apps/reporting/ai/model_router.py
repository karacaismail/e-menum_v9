"""
AI Model Router for selecting the optimal AI model per request.

Routes AI requests to the best model based on:
    - Report complexity (simple queries -> fast/cheap model)
    - Organization plan tier (higher tiers get better models)
    - Credit budget considerations
    - Feature-specific requirements

Usage:
    from apps.reporting.ai.model_router import AIModelRouter

    router = AIModelRouter()
    config = router.select_model(
        feature_key='RPT-AI-NLQ',
        org_plan='PROFESSIONAL',
        parameters={'complexity': 'high'},
    )
    # config = {
    #     'model_name': 'claude-3-sonnet-20240229',
    #     'provider': 'anthropic',
    #     'max_tokens': 2000,
    #     'estimated_credits': 3,
    # }

Critical Rules:
    - Always respect plan tier limits
    - Fall back to cheaper models when budget is constrained
    - Log model selection decisions for optimization
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# MODEL CONFIGURATIONS
# =============================================================================

# Available AI models with their capabilities and costs
MODEL_CONFIGS = {
    'claude-3-haiku': {
        'display_name': 'Claude 3 Haiku',
        'provider': 'anthropic',
        'model_id': 'claude-3-haiku-20240307',
        'tier': 'fast',
        'max_tokens': 1000,
        'credit_cost_per_call': 1,
        'capabilities': ['nlq', 'summary', 'classification'],
        'speed': 'fast',
        'quality': 'good',
        'min_plan': 'STARTER',
    },
    'claude-3-sonnet': {
        'display_name': 'Claude 3 Sonnet',
        'provider': 'anthropic',
        'model_id': 'claude-3-sonnet-20240229',
        'tier': 'balanced',
        'max_tokens': 2000,
        'credit_cost_per_call': 3,
        'capabilities': ['nlq', 'summary', 'insight', 'forecast', 'classification'],
        'speed': 'medium',
        'quality': 'very_good',
        'min_plan': 'PROFESSIONAL',
    },
    'claude-3-opus': {
        'display_name': 'Claude 3 Opus',
        'provider': 'anthropic',
        'model_id': 'claude-3-opus-20240229',
        'tier': 'powerful',
        'max_tokens': 4000,
        'credit_cost_per_call': 10,
        'capabilities': [
            'nlq', 'summary', 'insight', 'forecast',
            'classification', 'complex_analysis', 'benchmark',
        ],
        'speed': 'slow',
        'quality': 'excellent',
        'min_plan': 'BUSINESS',
    },
    'gpt-4o-mini': {
        'display_name': 'GPT-4o Mini',
        'provider': 'openai',
        'model_id': 'gpt-4o-mini',
        'tier': 'fast',
        'max_tokens': 1000,
        'credit_cost_per_call': 1,
        'capabilities': ['nlq', 'summary', 'classification'],
        'speed': 'fast',
        'quality': 'good',
        'min_plan': 'STARTER',
    },
    'gpt-4o': {
        'display_name': 'GPT-4o',
        'provider': 'openai',
        'model_id': 'gpt-4o',
        'tier': 'balanced',
        'max_tokens': 2000,
        'credit_cost_per_call': 3,
        'capabilities': ['nlq', 'summary', 'insight', 'forecast', 'classification'],
        'speed': 'medium',
        'quality': 'very_good',
        'min_plan': 'PROFESSIONAL',
    },
    'gemini-1.5-flash': {
        'display_name': 'Gemini 1.5 Flash',
        'provider': 'gemini',
        'model_id': 'gemini-1.5-flash',
        'tier': 'fast',
        'max_tokens': 1000,
        'credit_cost_per_call': 1,
        'capabilities': ['nlq', 'summary', 'classification'],
        'speed': 'fast',
        'quality': 'good',
        'min_plan': 'STARTER',
    },
    'gemini-1.5-pro': {
        'display_name': 'Gemini 1.5 Pro',
        'provider': 'gemini',
        'model_id': 'gemini-1.5-pro',
        'tier': 'balanced',
        'max_tokens': 2000,
        'credit_cost_per_call': 3,
        'capabilities': ['nlq', 'summary', 'insight', 'forecast', 'classification'],
        'speed': 'medium',
        'quality': 'very_good',
        'min_plan': 'PROFESSIONAL',
    },
}

# Feature-to-capability mapping
FEATURE_CAPABILITY_MAP = {
    'RPT-AI-NLQ': 'nlq',
    'RPT-AI-INSIGHT': 'insight',
    'RPT-AI-FORECAST': 'forecast',
    'RPT-AI-SEGMENT': 'classification',
    'RPT-AI-BENCHMARK': 'benchmark',
    'RPT-AI-SUMMARY': 'summary',
    'RPT-AI-VOICE': 'nlq',
    'RPT-AI-CONVERSATIONAL': 'nlq',
}

# Plan tier hierarchy (index = access level)
PLAN_TIERS = ['FREE', 'STARTER', 'PROFESSIONAL', 'BUSINESS', 'ENTERPRISE']

# Complexity-to-tier mapping
COMPLEXITY_TIER_MAP = {
    'simple': 'fast',
    'medium': 'balanced',
    'high': 'powerful',
    'complex': 'powerful',
}


class AIModelRouter:
    """
    Routes AI requests to the optimal model based on multiple factors.

    Selection algorithm:
        1. Determine required capability from feature key
        2. Filter models by capability and plan access
        3. Select best model based on complexity preference
        4. Fall back to cheaper model if budget is constrained
    """

    def select_model(
        self,
        feature_key: str,
        org_plan: str = 'STARTER',
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Select the best AI model for a given feature and context.

        Args:
            feature_key: Report feature key (e.g., 'RPT-AI-NLQ')
            org_plan: Organization's plan tier
            parameters: Optional parameters including:
                - complexity (str): 'simple', 'medium', 'high', 'complex'
                - max_credits (int): Maximum credits to spend
                - preferred_provider (str): 'anthropic', 'openai', 'gemini'

        Returns:
            dict with keys:
                - model_name (str): Internal model identifier
                - model_id (str): Provider-specific model ID
                - provider (str): AI provider name
                - max_tokens (int): Max output tokens
                - estimated_credits (int): Estimated credit cost
                - display_name (str): Human-readable model name
        """
        parameters = parameters or {}
        complexity = parameters.get('complexity', 'medium')
        max_credits = parameters.get('max_credits', None)
        preferred_provider = parameters.get('preferred_provider', None)

        # Step 1: Determine required capability
        required_capability = FEATURE_CAPABILITY_MAP.get(feature_key, 'nlq')

        # Step 2: Filter eligible models
        eligible = self._filter_eligible_models(
            required_capability=required_capability,
            org_plan=org_plan,
            max_credits=max_credits,
            preferred_provider=preferred_provider,
        )

        if not eligible:
            # Fall back to cheapest available model
            logger.warning(
                'No eligible models for feature=%s plan=%s, using fallback',
                feature_key, org_plan,
            )
            eligible = self._get_fallback_models()

        # Step 3: Select best model based on complexity
        preferred_tier = COMPLEXITY_TIER_MAP.get(complexity, 'balanced')
        selected = self._select_best_match(eligible, preferred_tier)

        if not selected:
            # Ultimate fallback
            selected = list(MODEL_CONFIGS.values())[0]
            selected_name = list(MODEL_CONFIGS.keys())[0]
        else:
            selected_name = selected.get('_key', '')

        logger.info(
            'Model selected: feature=%s plan=%s complexity=%s -> %s (%s)',
            feature_key, org_plan, complexity,
            selected_name, selected.get('provider', 'unknown'),
        )

        return {
            'model_name': selected_name,
            'model_id': selected.get('model_id', ''),
            'provider': selected.get('provider', ''),
            'max_tokens': selected.get('max_tokens', 1000),
            'estimated_credits': selected.get('credit_cost_per_call', 1),
            'display_name': selected.get('display_name', selected_name),
        }

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get all available model configurations.

        Returns:
            list of dicts with model details
        """
        result = []
        for key, config in MODEL_CONFIGS.items():
            result.append({
                'model_name': key,
                'display_name': config['display_name'],
                'provider': config['provider'],
                'model_id': config['model_id'],
                'tier': config['tier'],
                'credit_cost': config['credit_cost_per_call'],
                'capabilities': config['capabilities'],
                'speed': config['speed'],
                'quality': config['quality'],
                'min_plan': config['min_plan'],
            })
        return result

    def estimate_cost(
        self,
        feature_key: str,
        model_name: str = '',
    ) -> int:
        """
        Estimate the credit cost for a feature with a specific model.

        Args:
            feature_key: Report feature key
            model_name: Optional specific model name

        Returns:
            int: Estimated credit cost
        """
        if model_name and model_name in MODEL_CONFIGS:
            return MODEL_CONFIGS[model_name]['credit_cost_per_call']

        # Default cost based on feature complexity
        default_costs = {
            'RPT-AI-NLQ': 1,
            'RPT-AI-INSIGHT': 3,
            'RPT-AI-FORECAST': 5,
            'RPT-AI-SEGMENT': 3,
            'RPT-AI-BENCHMARK': 2,
            'RPT-AI-SUMMARY': 1,
            'RPT-AI-VOICE': 2,
            'RPT-AI-CONVERSATIONAL': 2,
        }
        return default_costs.get(feature_key, 1)

    # ─────────────────────────────────────────────────────────
    # INTERNAL METHODS
    # ─────────────────────────────────────────────────────────

    def _filter_eligible_models(
        self,
        required_capability: str,
        org_plan: str,
        max_credits: Optional[int] = None,
        preferred_provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter models by capability, plan, budget, and provider preference.

        Args:
            required_capability: The required AI capability
            org_plan: Organization plan tier
            max_credits: Maximum credit budget per call
            preferred_provider: Preferred AI provider

        Returns:
            list of eligible model configs (with _key added)
        """
        org_tier_idx = (
            PLAN_TIERS.index(org_plan) if org_plan in PLAN_TIERS else 0
        )
        eligible = []

        for key, config in MODEL_CONFIGS.items():
            # Check capability
            if required_capability not in config['capabilities']:
                continue

            # Check plan access
            model_tier_idx = (
                PLAN_TIERS.index(config['min_plan'])
                if config['min_plan'] in PLAN_TIERS
                else 0
            )
            if model_tier_idx > org_tier_idx:
                continue

            # Check budget
            if max_credits is not None and config['credit_cost_per_call'] > max_credits:
                continue

            # Prefer specified provider
            entry = dict(config)
            entry['_key'] = key
            if preferred_provider and config['provider'] == preferred_provider:
                entry['_preference_bonus'] = 10
            else:
                entry['_preference_bonus'] = 0

            eligible.append(entry)

        return eligible

    def _select_best_match(
        self,
        eligible: List[Dict[str, Any]],
        preferred_tier: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Select the best model from eligible candidates.

        Prefers models matching the preferred tier. If none match,
        selects the best available alternative.

        Args:
            eligible: List of eligible model configs
            preferred_tier: Preferred performance tier

        Returns:
            dict: Selected model config, or None
        """
        if not eligible:
            return None

        # Try to find exact tier match
        tier_matches = [m for m in eligible if m.get('tier') == preferred_tier]
        if tier_matches:
            # Sort by preference bonus then quality
            quality_order = {'excellent': 4, 'very_good': 3, 'good': 2, 'basic': 1}
            tier_matches.sort(
                key=lambda m: (
                    m.get('_preference_bonus', 0),
                    quality_order.get(m.get('quality', 'basic'), 0),
                ),
                reverse=True,
            )
            return tier_matches[0]

        # Fallback: closest tier with preference for cheaper
        tier_order = {'fast': 1, 'balanced': 2, 'powerful': 3}
        preferred_idx = tier_order.get(preferred_tier, 2)

        eligible.sort(
            key=lambda m: (
                abs(tier_order.get(m.get('tier', 'balanced'), 2) - preferred_idx),
                m.get('credit_cost_per_call', 99),
            ),
        )

        return eligible[0]

    def _get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        Get the cheapest available models as fallback.

        Returns:
            list: Model configs sorted by cost (cheapest first)
        """
        fallback = []
        for key, config in MODEL_CONFIGS.items():
            if config['tier'] == 'fast':
                entry = dict(config)
                entry['_key'] = key
                entry['_preference_bonus'] = 0
                fallback.append(entry)

        if not fallback:
            # If no fast tier, just use the first available
            key = list(MODEL_CONFIGS.keys())[0]
            entry = dict(MODEL_CONFIGS[key])
            entry['_key'] = key
            entry['_preference_bonus'] = 0
            fallback.append(entry)

        return fallback
