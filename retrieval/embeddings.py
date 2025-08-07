"""Embedding management for knowledge processing."""

import json
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
from config.settings import RAG_CONFIG


class EmbeddingManager:
    """Manages text embeddings for knowledge processing."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or RAG_CONFIG["embedding_model"]
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        print(f"🔄 Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
    
    def encode_text(self, text: str) -> List[float]:
        """Generate embedding for a text string."""
        if self.model is None:
            self._load_model()
        return self.model.encode(text).tolist()
    
    def encode_chunks(self, chunks: List[Dict[str, Any]]) -> List[PointStruct]:
        """Generate embeddings for a list of chunks and return Qdrant points."""
        if self.model is None:
            self._load_model()
        
        print(f"🧠 Generating embeddings for {len(chunks)} chunks...")
        points = []
        
        for i, chunk in enumerate(chunks):
            if i % 100 == 0:
                print(f"   Processing chunk {i+1}/{len(chunks)}")
            
            # Generate embedding for the content
            embedding = self.model.encode(chunk["content"]).tolist()
            
            # Create Qdrant point
            point = PointStruct(
                id=chunk["chunk_id"],
                vector=embedding,
                payload={
                    "page": chunk["page"],
                    "page_id": chunk["page_id"],
                    "header_path": chunk["header_path"],
                    "content": chunk["content"]  # Include content for retrieval
                }
            )
            points.append(point)
        
        return points
    
    def load_chunks_from_jsonl(self, jsonl_path: str) -> List[Dict[str, Any]]:
        """Load chunks from a JSONL file."""
        print(f"📖 Reading chunks from {jsonl_path}...")
        chunks = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))
        
        print(f"📊 Found {len(chunks)} chunks")
        return chunks 