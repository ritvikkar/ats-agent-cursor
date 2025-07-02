import pytest
from ats_agent.main import process_companies
from typing import List, Dict


def test_process_companies(tmp_path) -> None:
    """Test process_companies() with a mock file containing two company names."""
    test_file = tmp_path / "companies.txt"
    test_file.write_text("Acme Corp\nGlobex Inc\n")
    expected: List[Dict[str, str]] = [
        {"company": "Acme Corp"},
        {"company": "Globex Inc"}
    ]
    result = process_companies(str(test_file))
    assert result == expected

def test_main_placeholder() -> None:
    """Placeholder test for main module."""
    assert True 