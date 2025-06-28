"""Health data management for Personal AI Brain.

Provides a simple interface to store and retrieve health metrics in Notion.
"""

import json
from dataclasses import dataclass

from openai import OpenAI

import config

from db.notion_client import get_client
from db.registry import get_database_tags, build_notion_properties



@dataclass
class Record:
    """Represents a health metric record."""
    tag: str      # Select field in Notion
    log: str      # Text field in Notion


# Schema definition for health database
SCHEMA = {
    "database_id": "HEALTH_DB_ID",
    "fields": {
        "log": {
            "notion_name": "Log",
            "notion_type": "title"
        },
        "tag": {
            "notion_name": "Tag", 
            "notion_type": "select"
        }
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
    
    # Build properties from schema
    properties = build_notion_properties(record, SCHEMA)
    
    # Get database ID from config
    database_id = getattr(config, SCHEMA["database_id"])
    
    response = notion.pages.create(
        parent={"database_id": database_id},
        properties=properties
    )
    
    return response["id"]


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



def _parse_json_response(result_text: str) -> dict:
    """Helper to parse JSON response and handle markdown code blocks."""
    # Handle JSON wrapped in markdown code blocks
    if result_text.startswith('```json'):
        result_text = result_text.replace('```json\n', '').replace('\n```', '')
    elif result_text.startswith('```'):
        result_text = result_text.replace('```\n', '').replace('\n```', '')
    
    return json.loads(result_text)
