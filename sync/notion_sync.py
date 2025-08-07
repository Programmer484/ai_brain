"""Notion synchronization using Last Edited By detection.

Handles syncing of Notion content by detecting pages edited by humans (vs AI)
using the Last Edited By property and comparing against known AI user IDs.
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Set, Optional
from notion_client import Client
from utils.notion_client import get_client
from config.settings import KNOWLEDGE_DB_ID, HEALTH_DB_ID


class NotionSyncManager:
    """Manages synchronization between Notion and local storage."""
    
    def __init__(self, sync_metadata_file: str = "data/sync_metadata.json", ai_user_ids: List[str] = None):
        self.client = get_client()
        self.sync_metadata_file = sync_metadata_file
        self.metadata = self._load_metadata()
        # Store AI user IDs to distinguish from human edits
        self.ai_user_ids = ai_user_ids or []
    
    def _load_metadata(self) -> Dict:
        """Load sync metadata from file."""
        if os.path.exists(self.sync_metadata_file):
            with open(self.sync_metadata_file, 'r') as f:
                return json.load(f)
        return {"pages": {}, "last_sync": None}
    
    def _save_metadata(self):
        """Save sync metadata to file."""
        os.makedirs(os.path.dirname(self.sync_metadata_file), exist_ok=True)
        with open(self.sync_metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def get_human_edited_pages(self, database_id: str) -> List[Dict]:
        """Get pages that have been edited by humans (not AI) since last sync."""
        # Get pages edited after last sync timestamp
        last_sync = self.metadata.get("last_sync")
        
        if not last_sync:
            # First time sync - get all pages
            filter_params = {}
        else:
            # Build timestamp filter for pages edited after last sync
            filter_params = {
                "filter": {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {
                        "after": last_sync
                    }
                }
            }
        
        # Query database with filter
        response = self.client.databases.query(
            database_id=database_id,
            **filter_params
        )
        pages = response.get("results", [])
        
        # Handle pagination
        while response.get("has_more"):
            response = self.client.databases.query(
                database_id=database_id,
                start_cursor=response["next_cursor"],
                **filter_params
            )
            pages.extend(response.get("results", []))
        
        # Filter pages to only include those edited by humans
        human_edited_pages = []
        for page in pages:
            last_edited_by = page.get("last_edited_by", {})
            editor_id = last_edited_by.get("id")
            
            # If editor_id is not in our AI user IDs list, it's a human edit
            if editor_id and editor_id not in self.ai_user_ids:
                human_edited_pages.append(page)
        
        return human_edited_pages
    
    def add_ai_user_id(self, user_id: str):
        """Add a user ID to the list of AI users."""
        if user_id not in self.ai_user_ids:
            self.ai_user_ids.append(user_id)
    
    def remove_ai_user_id(self, user_id: str):
        """Remove a user ID from the list of AI users."""
        if user_id in self.ai_user_ids:
            self.ai_user_ids.remove(user_id)
    
    def _get_page_title(self, page: Dict) -> str:
        """Extract page title from Notion page object."""
        properties = page.get("properties", {})
        
        # Find the title property dynamically
        for _, prop_data in properties.items():
            if prop_data.get("type") == "title" and prop_data.get("title"):
                return prop_data["title"][0]["plain_text"]
        
        return "Untitled"
    
    def _update_page_metadata(self, page: Dict, database_id: str, filepath: str = None):
        """Update metadata for a successfully processed page."""
        page_id = page["id"]
        last_edited = page["last_edited_time"]
        
        self.metadata["pages"][page_id] = {
            "last_edited": last_edited,
            "database_id": database_id,
            "title": self._get_page_title(page),
            "filepath": filepath,
            "synced_at": datetime.now().isoformat()
        }
    
    def _save_as_markdown(self, page: Dict, content: str, output_dir: str = "data/resources") -> bool:
        """Save page content as markdown file."""
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate safe filename from page title
            title = self._get_page_title(page)
            # Remove special characters but keep spaces
            safe_title = re.sub(r'[^\w\s-]', '', title)
            safe_title = safe_title.strip()
            
            # Use full page ID for unique filename (matching export format)
            page_id = page["id"].replace('-', '')  # Full page ID without dashes
            filename = f"{safe_title} {page_id}.md"
            
            # Check if file already exists (by page ID)
            existing_file = self._find_file_by_page_id(page["id"], output_dir)
            if existing_file:
                filepath = existing_file
                print(f"    📝 Updating: {os.path.basename(existing_file)}")
            else:
                filepath = os.path.join(output_dir, filename)
                print(f"    📝 Creating: {filename}")
            
            # Write markdown content
            with open(filepath, 'w', encoding='utf-8') as f:
                # Add frontmatter with metadata
                f.write("---\n")
                f.write(f"title: {title}\n")
                f.write(f"notion_id: {page['id']}\n")
                f.write(f"last_edited: {page['last_edited_time']}\n")
                f.write(f"synced_at: {datetime.now().isoformat()}\n")
                f.write("---\n\n")
                f.write(content)
            
            print(f"    📝 Saved: {filename}")
            return filepath
            
        except Exception as e:
            print(f"    ❌ Error saving markdown: {e}")
            return None
    
    def _find_file_by_page_id(self, page_id: str, search_dir: str = "data/resources") -> Optional[str]:
        """Find existing markdown file by page ID."""
        try:
            page_metadata = self.metadata["pages"].get(page_id, {})
            filepath = page_metadata.get("filepath")
            
            if filepath and os.path.exists(filepath):
                return filepath
            return None
            
        except Exception as e:
            print(f"Error searching for file by page ID: {e}")
            return None
    
    def sync_database(self, database_id: str, processor) -> Dict:
        """Sync a specific database, processing only pages tagged with 'human edited'."""
        print(f"🔄 Checking for human edited pages in database {database_id}...")
        
        human_edited_pages = self.get_human_edited_pages(database_id)
        
        if not human_edited_pages:
            print("✅ No human edited pages found")
            return {"human_edited_pages": 0, "processed_pages": 0}
        
        print(f"📝 Found {len(human_edited_pages)} human edited pages")
        
        # Process changed pages
        processed_count = 0
        failed_pages = []
        
        for page in human_edited_pages:
            try:
                # Extract page content and process it
                content = self._extract_page_content(page)
                if content:
                    # Save as markdown file
                    filepath = self._save_as_markdown(page, content)
                    
                    if filepath:
                        # TODO: Integrate with your existing processor to update RAG database
                        # processor.process_markdown_file(filepath)
                        
                        processed_count += 1
                        
                        # Only update metadata after successful processing
                        self._update_page_metadata(page, database_id, filepath)
                        
                        print(f"  ✅ Processed: {self._get_page_title(page)}")
                    else:
                        print(f"  ⚠️  Failed to save markdown: {self._get_page_title(page)}")
                else:
                    print(f"  ⚠️  No content found: {self._get_page_title(page)}")
            except Exception as e:
                failed_pages.append({"page_id": page["id"], "title": self._get_page_title(page), "error": str(e)})
                print(f"  ❌ Error processing page {self._get_page_title(page)}: {e}")
        
        # Update last sync timestamp and save metadata if pages were processed
        if processed_count > 0:
            self.metadata["last_sync"] = datetime.now().isoformat()
            self._save_metadata()
        
        result = {
            "human_edited_pages": len(human_edited_pages),
            "processed_pages": processed_count,
            "failed_pages": len(failed_pages)
        }
        
        if failed_pages:
            result["failed_page_details"] = failed_pages
        
        return result
    
    def _extract_page_content(self, page: Dict) -> Optional[str]:
        """Extract content from a Notion page as markdown using notion2md library."""
        try:
            from notion2md.exporter.block import StringExporter  # type: ignore
            
            # Use notion2md to extract content as markdown
            exporter = StringExporter(
                block_id=page["id"],
                notion_client=self.client
            )
            markdown_content = exporter.export()
            
            return markdown_content if markdown_content else None
            
        except Exception as e:
            print(f"  ⚠️  Error extracting content with notion2md: {e}")
            return None
    
    def sync_page_before_ai_edit(self, page_id: str) -> Optional[str]:
        """Sync a specific page before AI edits it. Returns content if page was changed by human."""
        try:
            page = self.client.pages.retrieve(page_id=page_id)
            last_edited = page["last_edited_time"]
            last_edited_by = page.get("last_edited_by", {})
            editor_id = last_edited_by.get("id")
            
            # Check if page was edited by a human (not AI) since our last sync
            page_metadata = self.metadata["pages"].get(page_id, {})
            last_sync = page_metadata.get("last_edited")
            
            # If page was edited after our last sync AND by a human, sync it
            if (last_sync and last_edited > last_sync and 
                editor_id and editor_id not in self.ai_user_ids):
                
                print(f"  🔄 Human edit detected, syncing page before AI edit")
                content = self._extract_page_content(page)
                if content:
                    self._save_as_markdown(page, content)
                    self._update_page_metadata(page, page.get("parent", {}).get("database_id", "unknown"))
                
                return content
            
            return None
            
        except Exception as e:
            print(f"Error syncing page before AI edit: {e}")
            return None
    
    def force_full_sync(self, database_id: str, processor) -> Dict:
        """Force a full sync of all pages in a database."""
        print(f"🔄 Performing full sync of database {database_id}...")
        
        # Clear metadata for this database to force re-sync
        self.metadata["pages"] = {
            page_id: data for page_id, data in self.metadata["pages"].items()
            if data.get("database_id") != database_id
        }
        
        # Clear last_sync to get all pages
        old_last_sync = self.metadata.get("last_sync")
        self.metadata["last_sync"] = None
        
        result = self.sync_database(database_id, processor)
        
        # Restore last_sync if no pages were processed
        if result["processed_pages"] == 0 and old_last_sync:
            self.metadata["last_sync"] = old_last_sync
        
        return result
    
    def get_sync_status(self) -> Dict:
        """Get current sync status and statistics."""
        total_pages = len(self.metadata["pages"])
        databases = {}
        
        for page_data in self.metadata["pages"].values():
            db_id = page_data.get("database_id", "unknown")
            if db_id not in databases:
                databases[db_id] = 0
            databases[db_id] += 1
        
        return {
            "total_pages_tracked": total_pages,
            "databases": databases,
            "last_sync": self.metadata.get("last_sync"),
            "metadata_file": self.sync_metadata_file
        } 