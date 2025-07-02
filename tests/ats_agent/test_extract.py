import pytest
from ats_agent.extract import extract_job_postings, extract_apply_link
from typing import List, Optional
from unittest.mock import PropertyMock


def test_extract_job_postings(monkeypatch) -> None:
    """Test extract_job_postings with a mocked HTML page containing job and excluded links."""
    sample_html = '''
    <html><body>
        <a href="/jobs/123">Job 1</a>
        <a href="https://company.com/careers/456">Job 2</a>
        <a href="https://www.linkedin.com/jobs/view/789">LinkedIn Job</a>
        <a href="https://indeed.com/viewjob?jk=101">Indeed Job</a>
        <a href="/about">About Us</a>
        <a href="/careers/opening-789">Job 3</a>
    </body></html>
    '''

    class MockResponse:
        def __init__(self, text: str):
            self.text = text
        def raise_for_status(self) -> None:
            pass

    def mock_get(url: str, headers=None, timeout: int = 10):
        return MockResponse(sample_html)

    monkeypatch.setattr("requests.get", mock_get)

    result: List[str] = extract_job_postings("https://company.com/careers")
    expected_links = {
        "https://company.com/jobs/123",
        "https://company.com/careers/456",
        "https://company.com/careers/opening-789"
    }
    assert set(result) == expected_links
    assert all("linkedin.com" not in url and "indeed.com" not in url for url in result)
    assert len(result) == 3


def test_extract_apply_link_success(mocker: "MockerFixture") -> None:
    """Test extract_apply_link returns the final apply URL when an 'Apply' button is present."""
    mock_browser = mocker.Mock()
    mock_context = mocker.Mock()
    mock_page = mocker.Mock()
    mock_button = mocker.Mock()
    # Simulate button found and click for any button:has-text selector, None for link selectors
    def query_selector_side_effect(sel: str):
        print(f"[TEST DEBUG] query_selector called with: {sel}")
        if 'button:has-text' in sel:
            return mock_button
        if 'a:has-text' in sel:
            return None
        return None
    mock_page.query_selector.side_effect = query_selector_side_effect
    mock_button.click.return_value = None
    mock_page.wait_for_load_state.return_value = None
    # Simulate page.url changes after click using PropertyMock
    url_state = {"clicked": False}
    def click_side_effect():
        url_state["clicked"] = True
    mock_button.click.side_effect = click_side_effect
    url_property = PropertyMock(side_effect=lambda: "https://company.com/apply-final" if url_state["clicked"] else "https://company.com/job/123")
    type(mock_page).url = url_property
    # Patch context.new_page and browser.new_context at the correct import path
    mock_context.new_page.return_value = mock_page
    mock_browser.new_context.return_value = mock_context
    mock_playwright = mocker.Mock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_sync_playwright = mocker.Mock(return_value=mocker.Mock(__enter__=lambda s: mock_playwright, __exit__=lambda s, exc_type, exc_val, exc_tb: None))
    mocker.patch("playwright.sync_api.sync_playwright", mock_sync_playwright)
    mocker.patch("playwright.sync_api.Browser.new_context", lambda self, **kwargs: mock_context)
    mocker.patch("playwright.sync_api.BrowserContext.new_page", lambda self: mock_page)

    result: Optional[str] = extract_apply_link("https://company.com/job/123")
    print(f"[TEST DEBUG] extract_apply_link result: {result}")
    assert result == "https://company.com/apply-final"


def test_extract_apply_link_timeout(mocker: "MockerFixture") -> None:
    """Test extract_apply_link returns None if no apply button or link is found (timeout/failure)."""
    mock_browser = mocker.Mock()
    mock_context = mocker.Mock()
    mock_page = mocker.Mock()
    # Simulate no button or link found
    mock_page.query_selector.return_value = None
    mock_context.new_page.return_value = mock_page
    mock_browser.new_context.return_value = mock_context
    mock_playwright = mocker.Mock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_sync_playwright = mocker.Mock(return_value=mocker.Mock(__enter__=lambda s: mock_playwright, __exit__=lambda s, exc_type, exc_val, exc_tb: None))
    mocker.patch("playwright.sync_api.sync_playwright", mock_sync_playwright)
    mocker.patch("playwright.sync_api.Browser.new_context", lambda self, **kwargs: mock_context)
    mocker.patch("playwright.sync_api.BrowserContext.new_page", lambda self: mock_page)

    result: Optional[str] = extract_apply_link("https://company.com/job/123")
    assert result is None

def test_extract_placeholder() -> None:
    """Placeholder test for extract module."""
    assert True 