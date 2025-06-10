"""Knowledge data management for Personal AI Brain.

Provides a simple interface to store and retrieve knowledge entries in Notion.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
from db.notion_client import get_client
from config import NOTION_PAGE_ID

# For now, all DBs share this ID
DB_ID = NOTION_PAGE_ID


@dataclass
class KnowledgeRecord:
    """Represents a knowledge entry record."""
    text: str
    created_ts: datetime
    tags: List[str]


def create(record: KnowledgeRecord) -> str:
    """Create a new knowledge record in Notion.
    
    Args:
        record: KnowledgeRecord instance to create
        
    Returns:
        str: Page ID of the created record
        
    Raises:
        Exception: If Notion API call fails
    """
    notion = get_client()
    
    # Convert tags list to Notion multi_select format
    tag_options = [{"name": tag} for tag in record.tags]
    
    response = notion.pages.create(
        parent={"database_id": DB_ID},
        properties={
            "Text": {
                "title": [{"text": {"content": record.text}}]
            },
            "Created": {
                "date": {"start": record.created_ts.isoformat()}
            },
            "Tags": {
                "multi_select": tag_options
            }
        }
    )
    
    return response["id"]


def query(filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Query knowledge records from Notion.
    
    Args:
        filter_dict: Optional filter parameters for the query
        
    Returns:
        List[Dict]: Raw Notion page results
        
    Raises:
        Exception: If Notion API call fails
    """
    notion = get_client()
    
    query_params = {"database_id": DB_ID}
    if filter_dict:
        query_params["filter"] = filter_dict
    
    response = notion.databases.query(**query_params)
    return response["results"]


def update(page_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a knowledge record in Notion.
    
    Args:
        page_id: ID of the page to update
        data: Properties to update
        
    Returns:
        Dict: Updated page data from Notion
        
    Raises:
        Exception: If Notion API call fails
    """
    notion = get_client()
    
    response = notion.pages.update(
        page_id=page_id,
        properties=data
    )
    
    return response 