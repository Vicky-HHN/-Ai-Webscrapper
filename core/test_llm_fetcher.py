import pytest
from unittest.mock import MagicMock, patch
from core.llm_agent import LLMAgent
from core.fetcher import Fetcher

@patch('ollama.Client')
def test_llm_agent_interpret_prompt(mock_ollama_client):
    # Mock response
    mock_client_instance = mock_ollama_client.return_value
    mock_client_instance.chat.return_value = {
        'message': {
            'content': '{"url": "https://example.com", "fields": ["title"], "suggested_fields": [], "selectors": {"title": "h1"}}'
        }
    }

    agent = LLMAgent()
    result = agent.interpret_prompt("Test prompt")

    assert result['url'] == "https://example.com"
    assert "title" in result['fields']

@patch('requests.get')
def test_fetcher_scraperapi(mock_get):
    # Mock successful ScraperAPI response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>Content</html>"
    mock_get.return_value = mock_response

    with patch('core.fetcher.SCRAPERAPI_KEY', 'fake_key'):
        fetcher = Fetcher()
        content = fetcher.fetch("https://example.com")
        assert content == "<html>Content</html>"
        assert mock_get.called

@patch('requests.get')
def test_fetcher_fallback_to_playwright(mock_get):
    # Mock failure for ScraperAPI and ScrapingBee
    mock_get.return_value.status_code = 500

    with patch('core.fetcher.Fetcher._fetch_with_playwright') as mock_pw:
        mock_pw.return_value = "<html>Playwright Content</html>"
        fetcher = Fetcher()
        content = fetcher.fetch("https://example.com")
        assert content == "<html>Playwright Content</html>"
        mock_pw.assert_called_once()
