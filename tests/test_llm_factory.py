import pytest
import os
from unittest.mock import patch, Mock

from src.llm.factory import LLMFactory


class TestLLMFactory:
    """Test cases for LLMFactory"""
    
    def test_get_available_providers(self):
        """Test getting list of available providers"""
        providers = LLMFactory.get_available_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert isinstance(providers, list)
    
    @patch('src.llm.openai_provider.AsyncOpenAI')
    def test_create_openai_provider(self, mock_openai_client):
        """Test creating OpenAI provider"""
        mock_openai_client.return_value = Mock()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            provider = LLMFactory.create_provider("openai")
        
        assert provider is not None
        assert provider.__class__.__name__ == "OpenAIProvider"
        mock_openai_client.assert_called_once()
    
    @patch('src.llm.anthropic_provider.AsyncAnthropic')
    def test_create_anthropic_provider(self, mock_anthropic_client):
        """Test creating Anthropic provider"""
        mock_anthropic_client.return_value = Mock()
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            provider = LLMFactory.create_provider("anthropic")
        
        assert provider is not None
        assert provider.__class__.__name__ == "AnthropicProvider"
        mock_anthropic_client.assert_called_once()
    
    def test_create_provider_unknown(self):
        """Test creating provider with unknown name"""
        with pytest.raises(ValueError) as exc_info:
            LLMFactory.create_provider("unknown")
        
        assert "Unknown provider: unknown" in str(exc_info.value)
        assert "Available providers:" in str(exc_info.value)
    
    @patch('src.llm.anthropic_provider.AsyncAnthropic')
    def test_create_provider_from_env(self, mock_anthropic_client):
        """Test creating provider from environment variable"""
        mock_anthropic_client.return_value = Mock()
        
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-key"}):
            provider = LLMFactory.create_provider()  # No provider specified
        
        assert provider.__class__.__name__ == "AnthropicProvider"
        mock_anthropic_client.assert_called_once()
    
    @patch('src.llm.openai_provider.AsyncOpenAI')
    def test_create_provider_default(self, mock_openai_client):
        """Test creating provider with default (openai) when no env var set"""
        mock_openai_client.return_value = Mock()
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            if "LLM_PROVIDER" in os.environ:
                del os.environ["LLM_PROVIDER"]
            provider = LLMFactory.create_provider()
        
        assert provider.__class__.__name__ == "OpenAIProvider"
        mock_openai_client.assert_called_once()
    
    @patch('src.llm.openai_provider.AsyncOpenAI')
    def test_create_provider_with_api_key(self, mock_openai_client):
        """Test creating provider with API key argument"""
        mock_openai_client.return_value = Mock()
        
        provider = LLMFactory.create_provider("openai", api_key="test-key")
        
        assert provider.__class__.__name__ == "OpenAIProvider"
        mock_openai_client.assert_called_once_with(api_key="test-key")