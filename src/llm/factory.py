import os
from typing import Optional

from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


class LLMFactory:
    """Factory for creating LLM provider instances."""
    
    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }
    
    @classmethod
    def create_provider(
        self,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """Create an LLM provider instance."""
        provider_name = provider_name or os.getenv("LLM_PROVIDER", "openai")
        
        if provider_name not in self._providers:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available providers: {list(self._providers.keys())}"
            )
        
        provider_class = self._providers[provider_name]
        return provider_class(**kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return list(cls._providers.keys())