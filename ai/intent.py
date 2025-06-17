"""Intent classification using LLM with two-step approach: database selection then field extraction."""

import json
from openai import OpenAI
import config
from db.registry import get_database_descriptions, get_database_tags


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


def extract_health_fields(text: str) -> dict:
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


def extract_knowledge_fields(text: str) -> dict:
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


def _parse_json_response(result_text: str) -> dict:
    """Helper to parse JSON response and handle markdown code blocks."""
    # Handle JSON wrapped in markdown code blocks
    if result_text.startswith('```json'):
        result_text = result_text.replace('```json\n', '').replace('\n```', '')
    elif result_text.startswith('```'):
        result_text = result_text.replace('```\n', '').replace('\n```', '')
    
    return json.loads(result_text)


# Legacy function for backward compatibility (can be removed later)
def classify(text: str) -> dict:
    """
    Legacy classification function - combines database selection and field extraction.
    
    DEPRECATED: Use classify_database + extract_*_fields instead.
    """
    db = classify_database(text)
    
    if db == "health":
        fields = extract_health_fields(text)
        return {
            "db": db,
            "tag": fields["tag"],
            "needs_why": False  # Health records don't use needs_why
        }
    elif db == "knowledge":
        fields = extract_knowledge_fields(text)
        return {
            "db": db,
            "tag": fields["tag"],
            "needs_why": fields["needs_why"]
        }
    else:
        raise ValueError(f"Unknown database: {db}") 