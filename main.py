"""Main entrypoint for Personal AI Brain."""

import sys

import config
from db.notion_client import get_client
from ingest import cli


def smoke_test():
    """Run a smoke test that queries Knowledge DB and prints count."""
    try:
        notion = get_client()
        response = notion.databases.query(database_id=config.KNOWLEDGE_DB_ID)
        results = response["results"]
        print(f"Knowledge DB smoke test passed: {len(results)} records found")
        return True
    except Exception as e:
        print(f"Knowledge DB smoke test failed: {e}")
        return False


def main():
    """Main entry point for the application."""
    if len(sys.argv) > 1 and sys.argv[1] == "log":
        # Route to CLI for log command
        cli.main()
    elif len(sys.argv) > 1 and sys.argv[1] == "smoke":
        success = smoke_test()
        sys.exit(0 if success else 1)
    else:
        print("Hello, Personal AI")
        print("Available commands:")
        print("  python main.py log \"your text\"  - Log text to personal AI brain")
        print("  python main.py smoke             - Run smoke test on Knowledge DB")


if __name__ == "__main__":
    main() 