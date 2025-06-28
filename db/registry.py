"""Database registry for dynamic discovery of available databases."""

import importlib
from typing import Any, Dict, List


def get_available_databases() -> Dict[str, dict]:
    """
    Dynamically discover all available database modules and their metadata.
    
    Returns:
        dict: Database name -> metadata mapping
    """
    databases = {}
    
    # Dynamically discover all database modules (files ending with _db.py)
    db_modules = _discover_database_modules()
    
    for module_name in db_modules:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'DATABASE_INFO'):
                db_info = module.DATABASE_INFO
                databases[db_info["name"]] = {
                    "description": db_info["description"],
                    "tags": db_info["tags"],
                    "module": module
                }
        except ImportError:
            # Module doesn't exist, skip
            continue
    
    return databases


def _discover_database_modules() -> List[str]:
    """
    Discover all database modules in the db package (files ending with _db.py).
    
    Returns:
        List[str]: List of module names (e.g., ['db.health_db', 'db.knowledge_db'])
    """
    import os
    import pkgutil
    
    modules = []
    
    # Get the path to the db package
    db_path = os.path.dirname(__file__)
    
    # Scan for all .py files in the db directory
    for finder, name, ispkg in pkgutil.iter_modules([db_path]):
        # Only include modules that end with _db
        if name.endswith('_db'):
            module_name = f"db.{name}"
            modules.append(module_name)
    
    return modules


def get_database_descriptions() -> Dict[str, str]:
    """Get database name -> description mapping for prompts."""
    databases = get_available_databases()
    return {name: info["description"] for name, info in databases.items()}


def get_database_tags(db_name: str) -> List[str]:
    """Get available tags for a specific database."""
    databases = get_available_databases()
    return databases.get(db_name, {}).get("tags", [])


def get_database_module(db_name: str):
    """Get the module for a specific database."""
    databases = get_available_databases()
    return databases.get(db_name, {}).get("module")


def build_notion_properties(record, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Build Notion properties from a record using schema definition.
    
    Args:
        record: Record instance with data
        schema: Schema definition with field mappings
        
    Returns:
        Dict: Notion properties ready for API call
    """
    properties = {}
    
    for record_field, schema_config in schema["fields"].items():
        value = getattr(record, record_field)
        notion_name = schema_config["notion_name"]
        notion_type = schema_config["notion_type"]
        
        # === BASIC CONTENT TYPES ===
        if notion_type == "title":
            properties[notion_name] = {"title": [{"text": {"content": str(value)}}]}
        elif notion_type == "rich_text":
            properties[notion_name] = {"rich_text": [{"text": {"content": str(value)}}]}
        elif notion_type == "number":
            properties[notion_name] = {"number": value}
        elif notion_type == "checkbox":
            properties[notion_name] = {"checkbox": bool(value)}
            
        # === SELECTION TYPES ===
        elif notion_type == "select":
            properties[notion_name] = {"select": {"name": str(value)}}
        elif notion_type == "multi_select":
            # Expect value to always be a list
            properties[notion_name] = {"multi_select": [{"name": str(tag)} for tag in value]}
        elif notion_type == "status":
            properties[notion_name] = {"status": {"name": str(value)}}
            
        # === DATE/TIME TYPES ===
        elif notion_type == "date":
            if isinstance(value, dict):
                properties[notion_name] = {"date": value}  # {"start": "2023-01-01", "end": "2023-01-02"}
            else:
                properties[notion_name] = {"date": {"start": str(value)}}
        elif notion_type == "created_time":
            properties[notion_name] = {"created_time": {}}  # Read-only, auto-populated
        elif notion_type == "last_edited_time":
            properties[notion_name] = {"last_edited_time": {}}  # Read-only, auto-populated
            
        # === CONTACT/URL TYPES ===
        elif notion_type == "url":
            properties[notion_name] = {"url": str(value) if value else None}
        elif notion_type == "email":
            properties[notion_name] = {"email": str(value) if value else None}
        elif notion_type == "phone_number":
            properties[notion_name] = {"phone_number": str(value) if value else None}
            
        # === PEOPLE TYPES ===
        elif notion_type == "people":
            # Expect value to always be a list of user IDs
            properties[notion_name] = {"people": [{"id": str(person_id)} for person_id in value]}
        elif notion_type == "created_by":
            properties[notion_name] = {"created_by": {}}  # Read-only, auto-populated
        elif notion_type == "last_edited_by":
            properties[notion_name] = {"last_edited_by": {}}  # Read-only, auto-populated
            
        # === FILE TYPES ===
        elif notion_type == "files":
            # Expect value to always be a list of file names/URLs
            properties[notion_name] = {"files": [{"name": str(f)} for f in value]}
                
        # === RELATION TYPES ===
        elif notion_type == "relation":
            # Expect value to always be a list of relation IDs
            properties[notion_name] = {"relation": [{"id": str(rel_id)} for rel_id in value]}
        elif notion_type == "rollup":
            # Rollup is computed, typically read-only
            properties[notion_name] = {"rollup": {}}
        elif notion_type == "formula":
            # Formula is computed, read-only
            properties[notion_name] = {"formula": {}}
            
        # === UNSUPPORTED TYPE ===
        else:
            raise ValueError(f"Unsupported notion_type: {notion_type}")
        
    return properties 