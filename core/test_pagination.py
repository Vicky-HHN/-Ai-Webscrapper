import pytest
from unittest.mock import MagicMock, patch
from core.scraper import ScraperOrchestrator

def test_pagination_url_parameter():
    scraper = ScraperOrchestrator()
    current_url = "https://example.com/search?q=test"
    pagination = {'type': 'url_parameter', 'parameter_name': 'p'}

    next_url = scraper._get_next_url(current_url, "", pagination, 2)
    assert "p=2" in next_url
    assert "q=test" in next_url

def test_pagination_selector():
    scraper = ScraperOrchestrator()
    current_url = "https://example.com/page1"
    html = '<html><a class="next" href="/page2">Next</a></html>'
    pagination = {'type': 'selector', 'next_selector': 'a.next'}

    next_url = scraper._get_next_url(current_url, html, pagination, 2)
    assert next_url == "https://example.com/page2"

@patch('core.scraper.LLMAgent')
@patch('core.scraper.Fetcher')
@patch('core.scraper.Validator')
def test_multi_page_loop(mock_validator, mock_fetcher, mock_llm):
    # Setup mocks
    mock_llm_inst = mock_llm.return_value
    mock_llm_inst.interpret_prompt.return_value = {
        'url': 'https://example.com',
        'fields': ['title'],
        'selectors': {'title': 'h1'},
        'pagination': {'type': 'url_parameter', 'parameter_name': 'page', 'max_pages': 2}
    }
    mock_llm_inst.validate_data.return_value = {'is_valid': True}

    mock_fetcher_inst = mock_fetcher.return_value
    mock_fetcher_inst.fetch.side_effect = ["<html><h1>P1</h1></html>", "<html><h1>P2</h1></html>"]

    mock_val_inst = mock_validator.return_value
    mock_val_inst.validate_page.return_value = (True, "")
    mock_val_inst.validate_data.side_effect = lambda x: x
    mock_val_inst.deduplicate.side_effect = lambda x: x

    orchestrator = ScraperOrchestrator()
    # Mock exporter to avoid file creation
    orchestrator.exporter = MagicMock()
    orchestrator.exporter.export.return_value = ("json", "csv")

    result = orchestrator.run("test prompt")

    assert mock_fetcher_inst.fetch.call_count == 2
    assert len(result['records']) == 2
    assert result['records'][0]['title'] == 'P1'
    assert result['records'][1]['title'] == 'P2'
