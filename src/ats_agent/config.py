"""Configuration loader and environment variable management for ATS Agent.""" 

import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

# API Keys
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Headers and settings
HEADERS = {
    "User-Agent": os.getenv("USER_AGENT", "")
}
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
TIMEOUT = int(os.getenv("TIMEOUT", 10)) 