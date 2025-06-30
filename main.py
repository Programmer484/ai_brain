"""Main entrypoint for Personal AI Brain."""

import sys
import config
from db.notion_client import get_client
from ingest import cli


def main():
    """Main entry point for the application."""
    if len(sys.argv) > 1 and sys.argv[1] == "log":
        # Route to CLI for log command
        cli.main()
    else:
        print("Hello, Personal AI")
        print("Available commands:")
        print("  python main.py log \"your text\"  - Log text to personal AI brain")


if __name__ == "__main__":
    main() 