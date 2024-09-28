import unittest
from config import AzureLLMConfig

class MockAzureADTokenProvider:
    """A mock AzureADTokenProvider for testing purposes."""
    def get_token(self):
        return "mock_token"

def test_valid_config_with_api_key():
    """Test configuration where api_key is provided and azure_ad_token_provider is None."""
    config = AzureLLMConfig(
        name="my config",
        api_key="my_api_key",
        azure_ad_token_provider=None,
        api_version="2023-09-01",
        model_name="my-model",
        endpoint="https://example.azure.com"
    )
    assert config.api_key=="my_api_key"
    assert config.azure_ad_token_provider==None
    assert config.api_version=="2023-09-01"
    assert config.model_name=="my-model"
    assert config.endpoint=="https://example.azure.com"


def test_valid_config_with_ad_token_provider():
    """Test configuration where azure_ad_token_provider is provided and api_key is None."""
    mock_provider = MockAzureADTokenProvider()
    config = AzureLLMConfig(
        name="my config",
        api_key=None,
        azure_ad_token_provider=mock_provider,
        api_version="2023-09-01",
        model_name="my-model",
        endpoint="https://example.azure.com"
    )
    assert config.api_key==None
    assert config.azure_ad_token_provider==mock_provider
    assert config.api_version=="2023-09-01"
    assert config.model_name=="my-model"
    assert config.endpoint=="https://example.azure.com"

def test_missing_both_api_key_and_ad_token():
    """Test configuration where both api_key and azure_ad_token_provider are None, should raise ValueError."""
    try:
        AzureLLMConfig(
            name="my config",
            api_key=None,
            azure_ad_token_provider=None,
            api_version="2023-09-01",
            model_name="my-model",
            endpoint="https://example.azure.com"
        )
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert str(e) == "Either 'api_key' or 'azure_ad_token_provider' must be provided."

def test_post_init_resets_api_key_when_ad_token_provider_is_provided():
    """Test that providing azure_ad_token_provider resets api_key to None in the __post_init__ method."""
    mock_provider = MockAzureADTokenProvider()
    config = AzureLLMConfig(
        name="my config",
        api_key="my_api_key",
        azure_ad_token_provider=mock_provider,
        api_version="2023-09-01",
        model_name="my-model",
        endpoint="https://example.azure.com"
    )
    assert config.api_key==None
    assert config.azure_ad_token_provider==mock_provider
