"""Knowledge data management for Personal AI Brain.

Provides a simple interface to store and retrieve knowledge entries in Notion.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI

import config
from db.notion_client import get_client
from db.registry import get_database_tags, build_notion_properties


@dataclass
class Record:
    """Represents a knowledge entry record."""
    title: str        # Text field in Notion
    why: str          # Text field in Notion
    tags: List[str]   # Multi-select field in Notion


# Schema definition for knowledge database
SCHEMA = {
    "database_id": "KNOWLEDGE_DB_ID",
    "fields": {
        "title": {
            "notion_name": "Title",
            "notion_type": "title"
        },
        "tags": {
            "notion_name": "Tags",
            "notion_type": "multi_select"
        },
        "why": {
            "notion_name": "Why",
            "notion_type": "rich_text"
        }
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
    
    # Build properties from schema
    properties = build_notion_properties(record, SCHEMA)
    
    # Get database ID from config
    database_id = getattr(config, SCHEMA["database_id"])
    
    response = notion.pages.create(
        parent={"database_id": database_id},
        properties=properties
    )
    
    return response["id"]



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
    if fields["needs_why"]:
        why_answer = input("Why is this important? ")
    
    record = Record(
        title=fields["title"],
        why=why_answer,
        tags=[fields["tag"]]
    )
    return create(record)
