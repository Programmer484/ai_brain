"""Database registry for dynamic discovery of available databases."""

import importlib
from typing import Dict, List


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