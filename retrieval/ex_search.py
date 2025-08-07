"""Examples of using the flexible RAG search system."""

from qdrant_client import QdrantClient
from retrieval.search import RAGSearch
from config.settings import QDRANT_HOST, QDRANT_PORT

def create_search_client():
    """Create a RAGSearch client with proper dependencies."""
    client = QdrantClient(url=QDRANT_HOST, port=QDRANT_PORT)
    return RAGSearch(client)

def example_basic_search():
    """Basic search without filters."""
    rag = create_search_client()
    results = rag.search("machine learning algorithms", top_k=5)
    return results

def example_must_filter():
    """Search with 'must' filter - documents MUST match this condition."""
    rag = create_search_client()
    
    # Only return documents from the "AI" page
    filters = {
        "must": [
            {"key": "page", "match": {"value": "AI"}}
        ]
    }
    
    results = rag.search("neural networks", top_k=5, filters=filters)
    return results

def example_should_filter():
    """Search with 'should' filter - documents SHOULD match this condition (boosts relevance)."""
    rag = create_search_client()
    
    # Boost documents that contain "machine learning" or "deep learning"
    filters = {
        "should": [
            {"key": "content", "match": {"text": "machine learning"}},
            {"key": "content", "match": {"text": "deep learning"}}
        ]
    }
    
    results = rag.search("artificial intelligence", top_k=5, filters=filters)
    return results

def example_must_not_filter():
    """Search with 'must_not' filter - documents MUST NOT match this condition."""
    rag = create_search_client()
    
    # Exclude deprecated documents
    filters = {
        "must_not": [
            {"key": "page_id", "match": {"value": "deprecated"}}
        ]
    }
    
    results = rag.search("programming concepts", top_k=5, filters=filters)
    return results

def example_complex_filter():
    """Complex filter combining multiple operators."""
    rag = create_search_client()
    
    filters = {
        "must": [
            {"key": "page", "match": {"value": "AI"}},  # Must be from AI page
            {"key": "header_path", "match": {"text": "Machine Learning"}}  # Must be in ML section
        ],
        "should": [
            {"key": "content", "match": {"text": "neural networks"}},  # Boost if contains neural networks
            {"key": "content", "match": {"text": "deep learning"}}     # Boost if contains deep learning
        ],
        "must_not": [
            {"key": "page_id", "match": {"value": "deprecated"}},  # Don't include deprecated
            {"key": "content", "match": {"text": "outdated"}}      # Don't include outdated content
        ]
    }
    
    results = rag.search("artificial intelligence techniques", top_k=5, filters=filters)
    return results

def example_header_filter():
    """Filter by specific header path."""
    rag = create_search_client()
    
    # Only return documents under "AI/Introduction" header
    filters = {
        "must": [
            {"key": "header_path", "match": {"text": "AI/Introduction"}}
        ]
    }
    
    results = rag.search("what is artificial intelligence", top_k=5, filters=filters)
    return results

if __name__ == "__main__":
    # Example usage
    rag = create_search_client()
    
    print("=== Basic Search ===")
    results = example_basic_search()
    rag.display_results(results, "machine learning algorithms")
    
    print("\n=== Must Filter ===")
    results = example_must_filter()
    rag.display_results(results, "neural networks")
    
    print("\n=== Complex Filter ===")
    results = example_complex_filter()
    rag.display_results(results, "artificial intelligence techniques") 