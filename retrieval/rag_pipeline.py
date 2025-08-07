"""Notion RAG processing for AI Brain."""

import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from retrieval import TextChunker, EmbeddingManager, RAGSearch
from config.settings import RAG_CONFIG, QDRANT_HOST, QDRANT_PORT


class NotionProcessor:
    """Processes Notion content for RAG"""
    
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_HOST, port=QDRANT_PORT)
        self.chunker = TextChunker()
        self.embedding_manager = EmbeddingManager()
        self.search = RAGSearch(self.client)
    
    def setup(self):
        """Initialize the RAG base (Qdrant collection)."""
        self.search.setup_collection()
    
    def process_export(self, export_folder: str, output_jsonl: str = "data/chunks.jsonl"):
        """Process Notion export and create chunks."""
        if not os.path.exists(export_folder):
            raise FileNotFoundError(f"Export folder '{export_folder}' not found")
        
        chunks = self.chunker.chunk_all_md_files(export_folder)
        self.chunker.save_chunks_to_jsonl(chunks, output_jsonl)
        return chunks
    
    def load_to_qdrant(self, chunks_jsonl: str = "data/chunks.jsonl"):
        """Load chunks from JSONL file into Qdrant."""
        chunks = self.embedding_manager.load_chunks_from_jsonl(chunks_jsonl)
        points = self.embedding_manager.encode_chunks(chunks)
        
        self.search.client.upsert(
            collection_name=self.search.collection_name,
            points=points
        )
        return len(points)
    
    def setup_pipeline(self, export_folder: str):
        """Complete pipeline: setup → process → load."""
        self.setup()
        chunks = self.process_export(export_folder)
        points_count = self.load_to_qdrant()
        return {"chunks": len(chunks), "points": points_count}
    
    def search(self, query: str, top_k: int = 5, filters: Dict = None):
        """Search the RAG base."""
        return self.search.search_and_display(query, top_k, filters)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG base statistics."""
        return self.search.get_collection_info() 