"""Health data management for Personal AI Brain.

Provides a simple interface to store and retrieve health metrics in Notion.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import HEALTH_DB_ID
from db.notion_client import get_client
from db.registry import get_database_tags



@dataclass
class Record:
    """Represents a health metric record."""
    tag: str      # Select field in Notion
    log: str      # Text field in Notion


# Schema definition for health database
SCHEMA = {
    "update_fields": {
        "Tag": {"select": {"name": "updated_test"}}
    }
}

# Database metadata for dynamic discovery
DATABASE_INFO = {
    "name": "health",
    "description": "Physical/mental health, sleep, mood, exercise, diet, symptoms, medications",
    "tags": ["Sleep", "Exercise", "Mood", "Diet", "Symptoms", "Medication", "Misc"]  # Will import from predefined_tags later
}


def create(record: Record) -> str:
    """Create a new health record in Notion.
    
    Args:
        record: Record instance to create
        
    Returns:
        str: Page ID of the created record
        
    Raises:
        Exception: If Notion API call fails
    """
    notion = get_client()
        
    response = notion.pages.create(
        parent={"database_id": HEALTH_DB_ID},
        properties={
            "Log": {
                "title": [{"text": {"content": record.log}}]
            },
            "Tag": {
                "select": {"name": record.tag}
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
        
    query_params = {"database_id": HEALTH_DB_ID}
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


def _parse_json_response(result_text: str) -> dict:
    """Helper to parse JSON response and handle markdown code blocks."""
    # Handle JSON wrapped in markdown code blocks
    if result_text.startswith('```json'):
        result_text = result_text.replace('```json\n', '').replace('\n```', '')
    elif result_text.startswith('```'):
        result_text = result_text.replace('```\n', '').replace('\n```', '')
    
    return json.loads(result_text)


def extract_fields(text: str) -> dict:
    """
    Extract health-specific fields from text.
    
    Args:
        text: Raw input text
        
    Returns:
        dict with keys: "tag", "log"
    """
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    prompt = f"""
You are a health data extractor. Extract relevant fields from this health-related text.

Text: "{text}"

Available health tags: {get_database_tags("health")}

Rules:
1. Choose the most appropriate tag from the list above
2. Use "Misc" if no tag fits well
3. The log should be the original text (we'll store it as-is)

Respond with valid JSON:
{{"tag": "Sleep", "log": "{text}"}}
"""
    
    try:
        response = client.chat.completions.create(
            model=config.AI_CONFIG["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.AI_CONFIG["max_tokens"],
            temperature=config.AI_CONFIG["temperature"]
        )
        
        result_text = response.choices[0].message.content.strip()
        result = _parse_json_response(result_text)
        
        # Validate and clean up
        if "tag" not in result:
            raise ValueError("Missing 'tag' field")
            
        # Validate tag
        valid_tags = get_database_tags("health")
        if result["tag"] not in valid_tags:
            result["tag"] = config.AI_CONFIG["fallback_tag"]
            
        # Ensure log field exists
        result["log"] = result.get("log", text)
        
        return result
        
    except Exception as e:
        raise Exception(f"Health field extraction failed: {e}")


def create_from_text(text: str) -> str:
    """Create a health record from text input."""
    fields = extract_fields(text)
    record = Record(
        log=fields["log"],
        tag=fields["tag"]
    )
    return create(record)


def delete(page_id: str) -> bool:
    """Delete (archive) a health record in Notion.
    
    Args:
        page_id: ID of the page to delete
        
    Returns:
        bool: True if deletion was successful
        
    Raises:
        Exception: If Notion API call fails
    """
    notion = get_client()
        
    response = notion.pages.update(
        page_id=page_id,
        archived=True
    )
    
    return response.get("archived", False) 