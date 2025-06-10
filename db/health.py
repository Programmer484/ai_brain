"""Health data management for Personal AI Brain.

Provides a simple interface to store and retrieve health metrics in Notion.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Any, Optional
from db.notion_client import get_client
from config import NOTION_PAGE_ID

# For now, all DBs share this ID
DB_ID = NOTION_PAGE_ID


@dataclass
class HealthRecord:
    """Represents a health metric record."""
    date: date
    metric: str
    value: float


def create(record: HealthRecord) -> str:
    """Create a new health record in Notion.
    
    Args:
        record: HealthRecord instance to create
        
    Returns:
        str: Page ID of the created record
        
    Raises:
        Exception: If Notion API call fails
    """
    notion = get_client()
    
    response = notion.pages.create(
        parent={"database_id": DB_ID},
        properties={
            "Date": {
                "date": {"start": record.date.isoformat()}
            },
            "Metric": {
                "title": [{"text": {"content": record.metric}}]
            },
            "Value": {
                "number": record.value
            }
        }
    )
    
    return response["id"]


def query(filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Query health records from Notion.
    
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
    """Update a health record in Notion.
    
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