"""Notion client wrapper for Personal AI Brain.

Provides a thin wrapper around the official notion-client with authentication
from environment variables.
"""

from notion_client import Client
from config import NOTION_TOKEN

# Global variable to store the memoized client
_notion_client = None


def get_client():
    """Get or create a Notion client instance.
    
    Lazy-initialized on first call and memoized for subsequent calls.
    
    Returns:
        Client: Authenticated Notion client instance
        
    Raises:
        ValueError: If NOTION_TOKEN is not set
    """
    global _notion_client
    
    if _notion_client is None:
        if not NOTION_TOKEN:
            raise ValueError("NOTION_TOKEN environment variable is required")
        
        _notion_client = Client(auth=NOTION_TOKEN)
    
    return _notion_client