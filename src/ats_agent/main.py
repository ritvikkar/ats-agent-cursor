"""Main entry point for the ATS Agent application."""
from typing import List, Dict
from pprint import pprint
from ats_agent.search import search_career_page, is_staffing_agency
from ats_agent.extract import extract_job_postings

def process_companies(input_file: str) -> List[Dict[str, str]]:
    """Read company names from a text file and return a list of dicts with company names.

    Args:
        input_file (str): Path to the input text file containing company names, one per line.

    Returns:
        List[Dict[str, str]]: List of dictionaries, each with a 'company' key.
    """
    companies = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            name = line.strip()
            if name:
                companies.append({"company": name})
    return companies


def main() -> None:
    """Main entry point for running the ATS Agent. Processes companies and prints results."""
    companies = process_companies('test_companies.txt')
    for company in companies:
        name = company["company"]
        print(f"\n=== {name} ===")
        career_url = search_career_page(name)
        print(f"Career page: {career_url}")
        if career_url:
            import requests
            try:
                resp = requests.get(career_url, timeout=10)
                resp.raise_for_status()
                html = resp.text
            except Exception:
                html = ""
            staffing_status = is_staffing_agency(html)
            print(f"Staffing agency: {staffing_status}")
            job_links = extract_job_postings(career_url)
            print("Job links:")
            pprint(job_links)
        else:
            print("No career page found.")


if __name__ == "__main__":
    main() 