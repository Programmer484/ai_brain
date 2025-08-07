"""Intent classification using LLM with two-step approach: database selection then field extraction."""

import json
from openai import OpenAI
from config import settings as config
from databases.registry import get_database_descriptions, get_database_module


def classify_database(text: str) -> str:
    """
    First step: Determine which database this text belongs to.
    
    Args:
        text: Raw input text to classify
        
    Returns:
        str: Database name ("health", "knowledge", etc.)
    """
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    # Dynamically build available databases from registry
    db_descriptions = get_database_descriptions()
    db_list = "\n".join([f'- "{name}": {desc}' for name, desc in db_descriptions.items()])
    db_examples = ", ".join(db_descriptions.keys())
    
    prompt = f"""
    You are a database classifier for a personal AI brain system. Determine which database this text belongs to.

    Text to classify: "{text}"

    Available databases:
    {db_list}

    Respond with only the database name as a single word (no quotes, no JSON).
    Examples: {db_examples}
    """
    
    try:
        response = client.chat.completions.create(
            model=config.AI_CONFIG["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,  # Only need one word
            temperature=0.1  # Low temperature for consistent classification
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        # Validate result against available databases
        available_databases = list(get_database_descriptions().keys())
        if result not in available_databases:
            raise ValueError(f"Invalid database classification: {result}. Available: {available_databases}")
            
        return result
        
    except Exception as e:
        raise Exception(f"Database classification failed: {e}")


def _parse_json_response(result_text: str) -> dict:
    """Helper to parse JSON response and handle markdown code blocks."""
    # Handle JSON wrapped in markdown code blocks
    if result_text.startswith('```json'):
        result_text = result_text.replace('```json\n', '').replace('\n```', '')
    elif result_text.startswith('```'):
        result_text = result_text.replace('```\n', '').replace('\n```', '')
    
    return json.loads(result_text)
