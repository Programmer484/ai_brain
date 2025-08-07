"""Command line interface for ingesting data into the Personal AI Brain."""

import argparse
import sys
from ingestion.intent_classifier import classify_database
from databases.registry import get_database_module


def main():
    """Main CLI entry point for text ingestion."""
    parser = argparse.ArgumentParser(description="Personal AI Brain Text Ingestion")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add log subcommand
    log_parser = subparsers.add_parser("log", help="Log text to the personal AI brain")
    log_parser.add_argument("text", help="Text to log")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "log":
        handle_log_command(args.text)
    else:
        parser.print_help()
        sys.exit(1)


def handle_log_command(text: str):
    """Handle the log command using dynamic database discovery."""
    try:
        # Step 1: Determine which database this belongs to
        db_name = classify_database(text)
        
        # Step 2: Get the database module and let it handle everything
        db_module = get_database_module(db_name)
        if not db_module:
            raise ValueError(f"Unknown database: {db_name}")
        
        # Each database module handles its own field extraction and record creation
        page_id = db_module.create_from_text(text)
        print(f"✅ Saved to {db_name} database (ID: {page_id}).")
        
    except Exception as e:
        print(f"❌ Error saving entry: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 