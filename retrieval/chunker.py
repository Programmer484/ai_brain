"""Text chunking utilities for knowledge processing."""

import os
import re
import json
from typing import List, Dict, Any
from config.settings import RAG_CONFIG


def strip_page_id(name: str):
    """Extract page name and ID from filename (e.g. 'Page Name abc123' → ('Page Name', 'abc123'))."""
    parts = name.rsplit(" ", 1)
    if len(parts) == 2 and len(parts[1]) == 32:
        return parts[0], parts[1]
    return name, None


class TextChunker:
    """Handles text chunking for knowledge processing."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or RAG_CONFIG["chunk_size"]
        self.chunk_overlap = chunk_overlap or RAG_CONFIG["chunk_overlap"]
    
    def chunk_md_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Split a markdown file into semantic chunks while preserving header hierarchy.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        base = os.path.splitext(os.path.basename(file_path))[0]
        page, page_id = strip_page_id(base)

        lines = text.splitlines()
        header = None
        header_word_count = 0
        header_path = []
        current_chunk = []
        chunks = []
        word_count = 0
        chunk_id = 1

        def add_content_with_count(content: str):
            nonlocal word_count
            current_chunk.append(content)
            word_count += len(content.split())

        def flush_chunk():
            """Save current chunk to results and reset for next chunk."""
            nonlocal current_chunk, word_count, chunk_id
            content = "\n".join(current_chunk).strip()
            if content:
                chunks.append(
                    {
                        "page": page,
                        "page_id": page_id,
                        "chunk_id": chunk_id,
                        "header_path": header_path.copy() if header_path else ["No Header"],
                        "content": content,
                    }
                )
                chunk_id += 1
            current_chunk.clear()
            word_count = 0

        def start_new_chunk_with_header():
            """When a chunk flushes mid-section, start the next chunk with the current header for context."""
            nonlocal word_count
            if header:
                current_chunk.append(header)
                word_count = header_word_count

        # Iterate over each line
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            match = re.match(r"^(#{1,6}) (.+)", stripped)
            if match:
                # New header encountered
                flush_chunk()
                header = stripped
                header_word_count = len(stripped.split())

                level = len(match.group(1))
                header_text = match.group(2)

                header_path = header_path[: level - 1]  # truncate deeper levels
                header_path.append(header_text)         # append current level
                add_content_with_count(header)
            else:
                # Regular content
                add_content_with_count(stripped)
                if word_count >= self.chunk_size:
                    flush_chunk()
                    start_new_chunk_with_header()

        flush_chunk()  # flush remaining content
        return chunks
    
    def chunk_all_md_files(self, input_folder: str) -> List[Dict[str, Any]]:
        """Chunk all markdown files in a folder."""
        all_chunks = []
        
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"Input folder '{input_folder}' not found!")
        
        for filename in os.listdir(input_folder):
            if filename.endswith('.md'):
                file_path = os.path.join(input_folder, filename)
                chunks = self.chunk_md_file(file_path)
                all_chunks.extend(chunks)
        
        return all_chunks
    
    def save_chunks_to_jsonl(self, chunks: List[Dict[str, Any]], output_path: str):
        """Save chunks to JSONL format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n') 