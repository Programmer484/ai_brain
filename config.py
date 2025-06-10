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
OPENAI_KEY = os.getenv('OPENAI_KEY')

# Initialize basic logging to stdout (INFO level, timestamped)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
) 