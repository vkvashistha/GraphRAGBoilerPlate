"""Configuration management for the RAG system."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for RAG system settings."""
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL = "text-embedding-ada-002"
    GPT_MODEL = "gpt-4"
    
    # Vector Search Configuration
    VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "1536"))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD = 0.8
    
    # Text Processing Configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not cls.NEO4J_PASSWORD:
            raise ValueError("NEO4J_PASSWORD environment variable is required")