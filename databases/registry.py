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
        
        # Skip auto-populated/read-only fields - these cannot be set via API
        if notion_type in ["created_time", "last_edited_time", "created_by", "last_edited_by", "rollup", "formula"]:
            continue
        
        # Handle empty/null values consistently
        if value is None or (isinstance(value, str) and value.strip() == ""):
            continue
            
        # === BASIC CONTENT TYPES ===
        if notion_type == "title":
            properties[notion_name] = {"title": [{"text": {"content": str(value)}}]}
        elif notion_type == "rich_text":
            properties[notion_name] = {"rich_text": [{"text": {"content": str(value)}}]}
        elif notion_type == "number":
            if isinstance(value, (int, float)) and value != 0:  # Only include non-zero numbers
                properties[notion_name] = {"number": value}
        elif notion_type == "checkbox":
            properties[notion_name] = {"checkbox": bool(value)}
            
        # === SELECTION TYPES ===
        elif notion_type == "select":
            properties[notion_name] = {"select": {"name": str(value)}}
        elif notion_type == "multi_select":
            # Expect value to always be a list
            if isinstance(value, list) and value:
                properties[notion_name] = {"multi_select": [{"name": str(tag)} for tag in value if tag]}
        elif notion_type == "status":
            # Status is not a standard API type - using select instead
            # Note: This is a custom extension - consider updating schema to use 'select'
            properties[notion_name] = {"select": {"name": str(value)}}
            
        # === DATE/TIME TYPES ===
        elif notion_type == "date":
            if isinstance(value, dict):
                properties[notion_name] = {"date": value}  # {"start": "2023-01-01", "end": "2023-01-02"}
            else:
                properties[notion_name] = {"date": {"start": str(value)}}
            
        # === CONTACT/URL TYPES ===
        elif notion_type == "url":
            if value:
                properties[notion_name] = {"url": str(value)}
        elif notion_type == "email":
            if value:
                properties[notion_name] = {"email": str(value)}
        elif notion_type == "phone_number":
            if value:
                properties[notion_name] = {"phone_number": str(value)}
            
        # === PEOPLE TYPES ===
        elif notion_type == "people":
            # Expect value to always be a list of user IDs
            if isinstance(value, list) and value:
                properties[notion_name] = {"people": [{"id": str(person_id)} for person_id in value if person_id]}
            
        # === FILE TYPES ===
        elif notion_type == "files":
            # More complete format for files property
            if isinstance(value, list) and value:
                file_objects = []
                for f in value:
                    if isinstance(f, str):
                        # Simple file name/URL
                        if f.startswith(('http://', 'https://')):
                            file_objects.append({"type": "external", "name": f, "external": {"url": f}})
                        else:
                            file_objects.append({"type": "file", "name": f, "file": {"url": f}})
                    elif isinstance(f, dict):
                        # Already formatted file object
                        file_objects.append(f)
                if file_objects:
                    properties[notion_name] = {"files": file_objects}
                
        # === RELATION TYPES ===
        elif notion_type == "relation":
            # Expect value to always be a list of relation IDs
            if isinstance(value, list) and value:
                properties[notion_name] = {"relation": [{"id": str(rel_id)} for rel_id in value if rel_id]}
            
        # === UNSUPPORTED TYPE ===
        else:
            raise ValueError(f"Unsupported notion_type: {notion_type}")
        
    return properties


def get_database_descriptions() -> Dict[str, str]:
    """
    Get descriptions of all available databases.
    
    Returns:
        Dict[str, str]: Database name -> description mapping
    """
    databases = get_available_databases()
    return {name: info["description"] for name, info in databases.items()}


def get_database_module(db_name: str):
    """
    Get the database module for a given database name.
    
    Args:
        db_name: Name of the database
        
    Returns:
        Module: Database module or None if not found
    """
    databases = get_available_databases()
    return databases.get(db_name, {}).get("module")


def get_database_tags(db_name: str) -> List[str]:
    """
    Get the available tags for a specific database.
    
    Args:
        db_name: Name of the database
        
    Returns:
        List[str]: List of available tags for the database
    """
    databases = get_available_databases()
    return databases.get(db_name, {}).get("tags", [])


def _discover_database_modules() -> List[str]:
    """
    Discover all database modules in the databases package (files ending with _db.py).
    
    Returns:
        List[str]: List of module names (e.g., ['databases.health_db', 'databases.knowledge_db'])
    """
    import os
    import pkgutil
    
    modules = []
    
    # Get the path to the databases package
    db_path = os.path.dirname(__file__)
    
    # Scan for all .py files in the databases directory
    for _, name, _ in pkgutil.iter_modules([db_path]):
        # Only include modules that end with _db
        if name.endswith('_db'):
            module_name = f"databases.{name}"
            modules.append(module_name)
    
    return modules