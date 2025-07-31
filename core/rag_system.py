"""Core RAG system implementation with Neo4j backend."""
import logging
from typing import List, Dict, Any, Optional
from database.neo4j_client import Neo4jClient
from services.embedding_service import EmbeddingService
from services.document_processor import DocumentProcessor
from config import Config
import openai

logger = logging.getLogger(__name__)

class RAGSystem:
    """Retrieval-Augmented Generation system using Neo4j for storage and retrieval."""
    
    def __init__(self):
        """Initialize the RAG system with all required components."""
        logger.info("Initializing RAG system...")
        logger.info("Configuration loaded - Neo4j: %s, OpenAI: %s", 
                   Config.NEO4J_URI, 
                   "Configured" if Config.OPENAI_API_KEY else "Not Configured")
        self.db_client = Neo4jClient()
        self.embedding_service = EmbeddingService()
        self.document_processor = DocumentProcessor(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Initialize database schema
        self._setup_database()
    
    def _setup_database(self):
        """Set up the Neo4j database schema, constraints, and indexes."""
        logger.info("Setting up database schema...")
        self.db_client.create_constraints_and_indexes()
    
    def store_document(self, text: str, metadata: Dict[str, Any]) -> str:
        """
        Store a document by splitting into chunks, generating embeddings, 
        and creating graph relationships.
        
        Args:
            text: The document text to store
            metadata: Document metadata (source, author, topic, etc.)
            
        Returns:
            Document ID of the stored document
        """
        logger.info(f"Storing document with metadata: {metadata}")
        
        # Process document into chunks
        chunks = self.document_processor.create_document_chunks(text, metadata)
        
        # Generate embeddings for all chunks
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_service.embed_texts(chunk_texts)
        
        # Store chunks in Neo4j with relationships
        document_id = metadata.get('id', chunks[0]['id'])
        
        for chunk, embedding in zip(chunks, embeddings):
            self._store_chunk_with_relationships(chunk, embedding, metadata)
        
        logger.info(f"Successfully stored document {document_id} with {len(chunks)} chunks")
        return document_id
    
    def _store_chunk_with_relationships(self, chunk: Dict[str, Any], 
                                      embedding: List[float], 
                                      metadata: Dict[str, Any]):
        """Store a single chunk with its relationships in Neo4j."""
        
        # Create the document node with embedding
        create_doc_query = """
        CREATE (d:Document {
            id: $id,
            text: $text,
            embedding: $embedding,
            chunk_index: $chunk_index,
            total_chunks: $total_chunks,
            source: $source,
            topic: $topic,
            author: $author,
            created_at: datetime()
        })
        """
        
        params = {
            'id': chunk['id'],
            'text': chunk['text'],
            'embedding': embedding,
            'chunk_index': chunk['chunk_index'],
            'total_chunks': chunk['total_chunks'],
            'source': metadata.get('source', 'unknown'),
            'topic': metadata.get('topic', 'general'),
            'author': metadata.get('author', 'unknown')
        }
        
        self.db_client.execute_write_query(create_doc_query, params)
        
        # Create relationships
        self._create_author_relationship(chunk['id'], metadata.get('author'))
        self._create_topic_relationship(chunk['id'], metadata.get('topic'))
        
        # Extract and create concept/law relationships
        entities = self.document_processor.extract_entities(chunk['text'])
        self._create_concept_relationships(chunk['id'], entities['concepts'])
        self._create_law_relationships(chunk['id'], entities['laws'])
    
    def _create_author_relationship(self, doc_id: str, author: Optional[str]):
        """Create relationship between document and author."""
        if not author:
            return
        
        query = """
        MATCH (d:Document {id: $doc_id})
        MERGE (a:Author {name: $author})
        MERGE (a)-[:WROTE]->(d)
        """
        self.db_client.execute_write_query(query, {'doc_id': doc_id, 'author': author})
    
    def _create_topic_relationship(self, doc_id: str, topic: Optional[str]):
        """Create relationship between document and topic."""
        if not topic:
            return
        
        query = """
        MATCH (d:Document {id: $doc_id})
        MERGE (t:Topic {name: $topic})
        MERGE (d)-[:RELATED_TO]->(t)
        """
        self.db_client.execute_write_query(query, {'doc_id': doc_id, 'topic': topic})
    
    def _create_concept_relationships(self, doc_id: str, concepts: List[str]):
        """Create relationships between document and concepts."""
        for concept in concepts[:5]:  # Limit to top 5 concepts
            query = """
            MATCH (d:Document {id: $doc_id})
            MERGE (c:Concept {name: $concept})
            MERGE (d)-[:MENTIONS]->(c)
            """
            self.db_client.execute_write_query(query, {'doc_id': doc_id, 'concept': concept})
    
    def _create_law_relationships(self, doc_id: str, laws: List[str]):
        """Create relationships between document and laws."""
        for law in laws:
            query = """
            MATCH (d:Document {id: $doc_id})
            MERGE (l:Law {name: $law})
            MERGE (d)-[:CITES]->(l)
            """
            self.db_client.execute_write_query(query, {'doc_id': doc_id, 'law': law})