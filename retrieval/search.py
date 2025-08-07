"""RAG search functionality using Qdrant."""

import json
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
from config.settings import QDRANT_COLLECTION_NAME, RAG_CONFIG


class RAGSearch:
    """Handles semantic search using Qdrant for RAG functionality."""
    
    def __init__(self, client: QdrantClient, collection_name: str = None):
        self.client = client
        self.model = None
        self.collection_name = collection_name or QDRANT_COLLECTION_NAME
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        model_name = RAG_CONFIG["embedding_model"]
        self.model = SentenceTransformer(model_name)
    
    def setup_collection(self):
        """Initialize Qdrant collection if it doesn't exist."""
        collections = self.client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if self.collection_name in collection_names:
            print(f"✅ Collection '{self.collection_name}' already exists")
            return
        
        # Create collection with proper configuration
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=384,  # all-MiniLM-L6-v2 embedding size
                distance=Distance.COSINE,
                on_disk=False  # Keep in RAM for speed
            )
        )
        
        print(f"✅ Created collection '{self.collection_name}'")
    
    def search(self, query: str, top_k: int = 5, 
               filters: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar chunks with flexible filtering.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional filter conditions with logical operators
                    Example: {
                        "must": [{"key": "page", "match": {"value": "AI"}}],
                        "should": [{"key": "content", "match": {"text": "machine learning"}}],
                        "must_not": [{"key": "page_id", "match": {"value": "deprecated"}}]
                    }
            
        Returns:
            List of search results with content and metadata
        """
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Use provided filters or None
        search_filter = filters
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "score": result.score,
                "content": result.payload.get("content", ""),
                "page": result.payload.get("page", ""),
                "page_id": result.payload.get("page_id", ""),
                "header_path": result.payload.get("header_path", "")
            })
        
        return formatted_results
    
    def display_results(self, results: List[Dict[str, Any]], query: str, 
                       top_k: int = 5, filters: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        """Display search results in a formatted way."""
        print(f"🔎 Top {top_k} results for: '{query}'")
        if filters:
            print(f"🔧 Applied filters: {filters}")
        print()
        
        for i, result in enumerate(results):
            print(f"#{i+1}: {result['page']} > {result['header_path']}")
            print(f"Similarity: {result['score']:.3f}")
            print(f"Content: {result['content'][:200].strip()}...")
            print("—" * 40)
    
    def search_and_display(self, query: str, top_k: int = 5, 
                          filters: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        """Perform search and display results in one function."""
        results = self.search(query, top_k, filters)
        self.display_results(results, query, top_k, filters)
        return results
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": collection_info.name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "status": collection_info.status
            }
        except Exception as e:
            return {"error": str(e)} 