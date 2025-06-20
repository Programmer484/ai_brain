"""Configuration module for Personal AI Brain.

Loads environment variables and sets up logging.
"""

import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables as module-level constants
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HEALTH_DB_ID = os.getenv('HEALTH_DB_ID')
KNOWLEDGE_DB_ID = os.getenv('KNOWLEDGE_DB_ID')

# AI Configuration
AI_CONFIG = {
    "model": "gpt-4o-mini",
    "max_tokens": 100,
    "temperature": 0.1,
    "title_max_length": 50,  # For knowledge entries
    "fallback_tag": "Misc",  # Default tag when AI can't decide
}

# Initialize basic logging to stdout (INFO level, timestamped)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
) 