"""Module for search-related functionality in ATS Agent."""
from typing import Optional
import requests
import re
from ats_agent import config
from loguru import logger


def search_career_page(company_name: str) -> Optional[str]:
    """Search for the company's careers page using SerpAPI.

    Args:
        company_name (str): The name of the company to search for.

    Returns:
        Optional[str]: The URL of the first search result, or None if not found or on error.
    """
    api_key = config.SERPAPI_KEY
    if not api_key:
        return None
    params = {
        "engine": "google",
        "q": f"{company_name} careers site:.com",
        "api_key": api_key,
        "num": 1
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("organic_results", [])
        if results:
            return results[0].get("link")
    except Exception:
        pass
    return None


def is_staffing_agency(html: str) -> str:
    """Classify if the HTML content describes a staffing agency using regex and OpenAI.

    Args:
        html (str): The HTML content to analyze.

    Returns:
        str: 'Yes', 'No', or 'Unsure'.
    """
    patterns = [
        r"hire for clients",
        r"staffing agency",
        r"recruitment services",
        r"talent placement",
        r"temp staffing",
        r"employment services"
    ]
    for pattern in patterns:
        if re.search(pattern, html, re.IGNORECASE):
            logger.info(f"[Staffing] Regex matched pattern '{pattern}' in HTML. Returning 'Yes'.")
            return 'Yes'

    # If no regex match, use OpenAI
    openai_api_key = config.OPENAI_API_KEY
    if not openai_api_key:
        logger.info("[Staffing] No OpenAI API key set. Returning 'Unsure'.")
        return 'Unsure'
    try:
        import openai
        openai_client = openai.OpenAI(api_key=openai_api_key)
        prompt = (
            "Does the following page describe a staffing agency? Return one of: Yes, No, Unsure. TEXT: "
            + html[:4000]  # Limit context for token safety
        )
        logger.info("[Staffing] Calling OpenAI for staffing agency classification.")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=5,
            temperature=0
        )
        answer = response.choices[0].message.content.strip()
        logger.info(f"[Staffing] OpenAI response: '{answer}'")
        if answer in {"Yes", "No", "Unsure"}:
            return answer
        # Fallback: try to extract a valid answer
        for valid in ("Yes", "No", "Unsure"):
            if valid in answer:
                logger.info(f"[Staffing] Fallback: found '{valid}' in OpenAI response.")
                return valid
    except Exception as e:
        logger.warning(f"[Staffing] Exception during OpenAI call: {e}")
    logger.info("[Staffing] Returning 'Unsure' after all checks.")
    return 'Unsure' 