"""Module for extraction logic in ATS Agent."""
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ats_agent import config
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from loguru import logger

MAX_JOB_LINKS = 3


def is_job_description_page(html: str) -> bool:
    """Check if the HTML content looks like a job description page."""
    soup = BeautifulSoup(html, "lxml")
    # Look for a job title
    title = soup.find(["h1", "h2"], string=True)
    if not title or len(title.get_text(strip=True)) < 4:
        return False
    # Look for job description keywords
    text = soup.get_text(" ", strip=True).lower()
    if any(kw in text for kw in ["responsibilities", "requirements", "description", "apply"]):
        # Look for an apply button or link
        if soup.find("a", string=lambda s: s and "apply" in s.lower()) or \
           soup.find("button", string=lambda s: s and "apply" in s.lower()):
            return True
    return False


def extract_job_postings(career_page_url: str) -> List[str]:
    """Extract up to MAX_JOB_LINKS unique job description URLs from a career page using advanced heuristics.

    Uses Playwright to render the page and extract links after JavaScript has run. Falls back to requests+BeautifulSoup if Playwright fails.
    Recursively follows subpages likely to contain job listings if needed.
    Logs detailed information for debugging.

    Args:
        career_page_url (str): The URL of the company's career page.

    Returns:
        List[str]: A list of up to MAX_JOB_LINKS deduplicated job description URLs.
    """
    job_links = set()
    visited = set()
    
    # Expanded job patterns and known ATS domains
    job_patterns = [
        "/job/", "/jobs/", "/position/", "/positions/", "/opening/", "/openings/", "/vacancy/", "/vacancies/", "/opportunity/", "/opportunities/", "/employment/", "/listing/", "/recruitment/", "/join-us/", "/apply/", "/career-areas/", "/job-search/", "/search-jobs/", "/viewjobs/", "/en/job/", "/en/jobs/", "/en/careers/"
    ]
    ats_domains = [
        "myworkdayjobs.com", "icims.com", "successfactors.com", "hr.cloud.sap", "greenhouse.io", "csod.com", "taleo.net", "avature.net", "workable.com", "oraclecloud.com", "lever.co", "smartrecruiters.com", "teamtailor.com", "applytojob.com", "recruitee.com", "talemetry.com", "jobadder.com", "jobdiva.com", "jobvite.com", "gupy.io"
    ]
    exclude_patterns = ["/about", "/life-at-", "#", "/events", "/internships", "/privacy", "/terms", "/contact", "/media", "/news", "/brand", "/faq", "/legal"]
    exclude_domains = [
        "linkedin.com", "indeed.com", "glassdoor.com", "monster.com", "ziprecruiter.com", "facebook.com", "twitter.com", "youtube.com", "instagram.com"
    ]
    subpage_text_patterns = [
        "job search", "search jobs", "view jobs", "open positions", "openings", "find jobs", "apply now", "career opportunities", "see jobs", "explore jobs", "current openings", "join our team"
    ]

    def extract_links_from_html(html: str, base_url: str) -> List[dict]:
        soup = BeautifulSoup(html, "lxml")
        a_tags = soup.find_all("a", href=True)
        links = []
        for a in a_tags:
            href = a["href"].strip()
            text = a.get_text(strip=True)
            url = urljoin(base_url, href)
            links.append({"url": url, "href": href, "text": text})
        return links

    def should_exclude(url: str) -> bool:
        return any(domain in url for domain in exclude_domains)

    def is_candidate_job_link(link: dict) -> bool:
        url = link["url"].lower()
        href = link["href"].lower()
        text = link["text"].lower()
        # Exclude aggregators and nav pages
        if should_exclude(url):
            return False
        if any(pat in url for pat in exclude_patterns):
            return False
        # Direct ATS domain
        if any(domain in url for domain in ats_domains):
            return True
        # Job patterns in url or href
        if any(pat in url for pat in job_patterns) or any(pat in href for pat in job_patterns):
            return True
        # Job-related text
        if any(pat in text for pat in subpage_text_patterns):
            return True
        return False

    def is_subpage_link(link: dict) -> bool:
        url = link["url"].lower()
        href = link["href"].lower()
        text = link["text"].lower()
        # Exclude aggregators and nav pages
        if should_exclude(url):
            return False
        if any(pat in url for pat in exclude_patterns):
            return False
        # Subpage text patterns
        return any(pat in text for pat in subpage_text_patterns) or any(pat in href for pat in subpage_text_patterns)

    def fetch_html(url: str) -> Optional[str]:
        try:
            resp = requests.get(url, headers=config.HEADERS, timeout=config.TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def extract_jobs_recursive(url: str, depth: int = 0):
        if url in visited or len(job_links) >= MAX_JOB_LINKS or depth > 2:
            return
        visited.add(url)
        html = None
        # Try Playwright first
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=config.HEADERS.get("User-Agent") or None, ignore_https_errors=True)
                page = context.new_page()
                page.set_default_timeout(config.TIMEOUT * 1000)
                page.goto(url)
                page.wait_for_load_state("networkidle", timeout=config.TIMEOUT * 1000)
                html = page.content()
                logger.info(f"[Playwright] Rendered HTML (first 500 chars): {html[:500]}")
                context.close()
                browser.close()
        except Exception as e:
            logger.warning(f"Playwright failed for {url}: {e}")
        if not html:
            html = fetch_html(url)
            if html:
                logger.info(f"[Requests] Fetched HTML (first 500 chars): {html[:500]}")
        if not html:
            return
        links = extract_links_from_html(html, url)
        logger.info(f"[Extract] Found {len(links)} <a> tags on {url}")
        # First, try to extract job links
        for link in links:
            logger.info(f"[Extract] Link: {link['url']} | Text: {link['text']} | Href: {link['href']}")
            if is_candidate_job_link(link):
                if link["url"] not in job_links:
                    # Content-based check
                    job_html = fetch_html(link["url"])
                    if job_html and is_job_description_page(job_html):
                        job_links.add(link["url"])
                        logger.info(f"[Content] Job description page found: {link['url']}")
                        if len(job_links) >= MAX_JOB_LINKS:
                            return
        # If not enough jobs, follow subpages recursively
        if len(job_links) < MAX_JOB_LINKS and depth < 2:
            for link in links:
                if is_subpage_link(link) and link["url"] not in visited:
                    logger.info(f"[Recursive] Following subpage link: {link['url']} | Text: {link['text']}")
                    extract_jobs_recursive(link["url"], depth + 1)
                    if len(job_links) >= MAX_JOB_LINKS:
                        return

    extract_jobs_recursive(career_page_url)
    return list(job_links)


def extract_apply_link(job_url: str) -> Optional[str]:
    """Extract the final apply destination URL from a job posting using Playwright.

    Launches a headless Chromium browser, navigates to the job_url, and searches for a button or link
    containing text like 'Apply', 'Apply Now', 'Submit Application', 'Start Application', or 'Continue'.
    If found, clicks or follows the link and returns the final resolved URL.

    Args:
        job_url (str): The URL of the job posting page.

    Returns:
        Optional[str]: The final apply destination URL, or None if not found or on error.
    """
    apply_texts = [
        "Apply", "Apply Now", "Submit Application", "Start Application", "Continue"
    ]
    browser = None
    context = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=config.HEADERS.get("User-Agent") or None,
                ignore_https_errors=True,
            )
            page = context.new_page()
            page.set_default_timeout(config.TIMEOUT * 1000)  # ms
            page.goto(job_url)

            print(f"[DEBUG] Navigated to {job_url}, starting apply_texts loop")
            print(f"[DEBUG] apply_texts: {apply_texts}")
            print(f"[DEBUG] type(page): {type(page)}")
            # Try to find and click/follow an apply button or link
            for text in apply_texts:
                print(f"[DEBUG] Entering loop for text: {text}")
                # Try button
                try:
                    button = page.query_selector(f'button:has-text("{text}")')
                    if button:
                        print(f"[DEBUG] Found button for text: {text}")
                        button.click()
                        page.wait_for_load_state("networkidle", timeout=config.TIMEOUT * 1000)
                        print(f"[DEBUG] After click, page.url = {page.url}")
                        return page.url
                except PlaywrightTimeoutError:
                    continue
                # Try link
                try:
                    link = page.query_selector(f'a:has-text("{text}")')
                    if link:
                        href = link.get_attribute("href")
                        if href:
                            # Follow the link if it's not a JS action
                            if not href.startswith("javascript:"):
                                page.goto(href)
                                page.wait_for_load_state("networkidle", timeout=config.TIMEOUT * 1000)
                                print(f"[DEBUG] After following link, page.url = {page.url}")
                                return page.url
                except PlaywrightTimeoutError:
                    continue
            # If nothing found, return the current page URL if it changed
            print("[DEBUG] No apply button or link found.")
            return None
    except Exception as e:
        print(f"[DEBUG] Exception in extract_apply_link: {e}")
        return None
    finally:
        try:
            if context is not None:
                context.close()
            if browser is not None:
                browser.close()
        except Exception:
            pass 