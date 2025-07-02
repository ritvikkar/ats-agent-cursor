import pytest
from typing import Optional
from ats_agent.search import search_career_page, is_staffing_agency


def test_search_career_page_returns_url(mocker) -> None:
    """Test search_career_page returns the first result URL using a mocked SerpAPI response."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "organic_results": [
            {"link": "https://acme.com/careers"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_response)
    
    result: Optional[str] = search_career_page("Acme Corp")
    assert result == "https://acme.com/careers"


def test_is_staffing_agency_regex_match() -> None:
    """Test is_staffing_agency returns 'Yes' when staffing keywords are present in HTML."""
    html = "<html><body>We are a staffing agency that provides recruitment services for top talent.</body></html>"
    result = is_staffing_agency(html)
    assert result == 'Yes'


def test_search_placeholder() -> None:
    """Placeholder test for search module."""
    assert True 