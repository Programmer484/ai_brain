"""Knowledge data management for Personal AI Brain.

Provides a simple interface to store and retrieve knowledge entries in Notion.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import KNOWLEDGE_DB_ID
from db.notion_client import get_client
from db.registry import get_database_tags


@dataclass
class Record:
    """Represents a knowledge entry record."""
    title: str        # Text field in Notion
    why: str          # Text field in Notion
    tags: List[str]   # Multi-select field in Notion


# Schema definition for knowledge database
SCHEMA = {
    "update_fields": {
        "Tags": {"multi_select": [{"name": "updated"}]}
    }
}

# Database metadata for dynamic discovery  
DATABASE_INFO = {
    "name": "knowledge",
    "description": "Information, ideas, references, learnings, actionable items, notes",
    "tags": ["Reference", "Idea", "Actionable", "Learning", "Note", "Misc"]  # Will import from predefined_tags later
}


def create(record: Record) -> str:
    """Create a new knowledge record in Notion.
    
    Args:
        record: Record instance to create
        
    Returns:
        str: Page ID of the created record
        
    Raises:
        Exception: If Notion API call fails
    """
    notion = get_client()
        
    # Convert tags list to Notion multi_select format
    tag_options = [{"name": tag} for tag in record.tags]
    
    response = notion.pages.create(
        parent={"database_id": KNOWLEDGE_DB_ID},
        properties={
            "Title": {
                "title": [{"text": {"content": record.title}}]
            },
            "Tags": {
                "multi_select": tag_options
            },
            "Why": {
                "rich_text": [{"text": {"content": record.why}}]
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
        
    query_params = {"database_id": KNOWLEDGE_DB_ID}
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
    Extract knowledge-specific fields from text.
    
    Args:
        text: Raw input text
        
    Returns:
        dict with keys: "tag", "title", "needs_why"
    """
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    prompt = f"""
You are a knowledge data extractor. Extract relevant fields from this knowledge-related text.

Text: "{text}"

Available knowledge tags: {get_database_tags("knowledge")}

Rules:
1. Choose the most appropriate tag from the list above
2. Use "Misc" if no tag fits well  
3. Create a concise title (max {config.AI_CONFIG["title_max_length"]} chars)
4. Set "needs_why" to true if the text lacks explanation/reasoning and would benefit from user clarification

Respond with valid JSON:
{{"tag": "Reference", "title": "Short descriptive title", "needs_why": false}}
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
        required_fields = ["tag", "title", "needs_why"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing '{field}' field")
        
        # Validate tag
        valid_tags = get_database_tags("knowledge")
        if result["tag"] not in valid_tags:
            result["tag"] = config.AI_CONFIG["fallback_tag"]
            
        # Truncate title if needed
        max_length = config.AI_CONFIG["title_max_length"]
        if len(result["title"]) > max_length:
            result["title"] = result["title"][:max_length]
            
        return result
        
    except Exception as e:
        raise Exception(f"Knowledge field extraction failed: {e}")


def create_from_text(text: str) -> str:
    """Create a knowledge record from text input."""
    fields = extract_fields(text)
    
    # Handle the "why" prompting if needed
    final_text = text
    if fields["needs_why"]:
        why_answer = input("Why is this important? ")
        final_text = f"{text}\nWhy: {why_answer}"
    
    record = Record(
        title=fields["title"],
        why=final_text,
        tags=[fields["tag"]]
    )
    return create(record)


def delete(page_id: str) -> bool:
    """Delete (archive) a knowledge record in Notion.
    
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