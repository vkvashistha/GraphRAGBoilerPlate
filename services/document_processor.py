"""Document processing service for text chunking and preparation."""
import re
import uuid
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing documents into chunks suitable for embedding."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize document processor with chunking parameters."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        # Clean the text
        text = self._clean_text(text)
        
        # Split by sentences to maintain semantic meaning
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_length += sentence_length
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and normalizing."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\']', ' ', text)
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Simple sentence splitting on periods, exclamation marks, question marks
        sentences = re.split(r'[.!?]+', text)
        # Filter out empty sentences and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get the last `overlap_size` characters as overlap text."""
        if len(text) <= overlap_size:
            return text
        return text[-overlap_size:]
    
    def create_document_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create document chunks with metadata and UUIDs."""
        chunks = self.split_text(text)
        document_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk_data = {
                'id': str(uuid.uuid4()),
                'text': chunk,
                'chunk_index': i,
                'total_chunks': len(chunks),
                **metadata  # Include all provided metadata
            }
            document_chunks.append(chunk_data)
        
        return document_chunks
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract basic entities from text (concepts, potential law references)."""
        # Simple regex-based entity extraction
        entities = {
            'concepts': [],
            'laws': [],
            'topics': []
        }
        
        # Extract potential law references (e.g., "Section 123", "Article 5", "USC 1234")
        law_patterns = [
            r'Section\s+\d+',
            r'Article\s+\d+',
            r'USC\s+\d+',
            r'Title\s+\d+',
            r'Chapter\s+\d+'
        ]
        
        for pattern in law_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['laws'].extend(matches)
        
        # Extract capitalized phrases as potential concepts (basic NER)
        concept_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        concepts = re.findall(concept_pattern, text)
        # Filter out common words and keep meaningful concepts
        meaningful_concepts = [c for c in concepts if len(c.split()) <= 3 and len(c) > 3]
        entities['concepts'] = list(set(meaningful_concepts))
        
        return entities