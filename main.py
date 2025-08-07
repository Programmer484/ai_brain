"""Main entrypoint for Personal AI Brain."""

import sys
import argparse
from ingestion import cli
from retrieval.rag_pipeline import NotionProcessor
from data.sync.notion_sync import NotionSyncManager


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Personal AI Brain")
    parser.add_argument("command", choices=["log", "rag-setup", "rag-search", "rag-stats", "sync", "sync-status"],
                       help="Command to run")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    
    if len(sys.argv) == 1:
        # No arguments provided, show help
        print("Hello, Personal AI Brain")
        print("Available commands:")
        print("  python main.py log \"your text\"                    - Log text to personal AI brain")
        print("  python main.py rag-setup <export_folder>           - Setup RAG base from Notion export")
        print("  python main.py rag-search \"your query\"             - Search RAG base")
        print("  python main.py rag-stats                           - Show RAG base statistics")
        print("  python main.py sync [database_id]                  - Sync changes from Notion database")
        print("  python main.py sync-status                         - Show sync status")
        return
    
    args = parser.parse_args()
    
    if args.command == "log":
        # Route to CLI for log command
        cli.main()
    
    elif args.command == "rag-setup":
        if not args.args:
            print("❌ Error: rag-setup requires an export folder path")
            print("Usage: python main.py rag-setup <export_folder>")
            return
        
        export_folder = args.args[0]
        processor = NotionProcessor()
        processor.full_setup_pipeline(export_folder)
    
    elif args.command == "rag-search":
        if not args.args:
            print("❌ Error: rag-search requires a query")
            print("Usage: python main.py rag-search \"your query\"")
            return
        
        query = args.args[0]
        processor = NotionProcessor()
        processor.search_rag(query)
    
    elif args.command == "rag-stats":
        processor = NotionProcessor()
        stats = processor.get_stats()
        print("📊 RAG Base Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    elif args.command == "sync":
        from config.settings import KNOWLEDGE_DB_ID, HEALTH_DB_ID
        
        # Use provided database ID or default to knowledge database
        if args.args:
            database_id = args.args[0]
        elif KNOWLEDGE_DB_ID:
            database_id = KNOWLEDGE_DB_ID
            print(f"🔄 Using knowledge database: {database_id}")
        else:
            print("❌ Error: No database ID provided and KNOWLEDGE_DB_ID not set")
            print("Usage: python main.py sync <database_id>")
            print("Or set KNOWLEDGE_DB_ID in your .env file")
            return
        
        sync_manager = NotionSyncManager()
        processor = NotionProcessor()  # TODO: Integrate with RAG pipeline
        result = sync_manager.sync_database(database_id, processor)
        
        print(f"✅ Sync completed:")
        print(f"  📝 Changed pages: {result['changed_pages']}")
        print(f"  ✅ Processed pages: {result['processed_pages']}")
        print(f"  ❌ Failed pages: {result['failed_pages']}")
        
        if result.get('failed_page_details'):
            print("  📋 Failed page details:")
            for failed in result['failed_page_details']:
                print(f"    - {failed['title']}: {failed['error']}")
    
    elif args.command == "sync-status":
        sync_manager = NotionSyncManager()
        status = sync_manager.get_sync_status()
        print("📊 Sync Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main() 