"""Neo4j database client and connection management."""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging
from config import Config

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Neo4j database client with connection management and query execution."""
    
    def __init__(self):
        """Initialize Neo4j client with configuration."""
        self.driver = None
        self.connect()
    
    def connect(self):
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Successfully connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if parameters is None:
            parameters = {}
        
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [dict(record) for record in result]
    
    def execute_write_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a write query in a transaction."""
        if parameters is None:
            parameters = {}
        
        with self.driver.session() as session:
            result = session.write_transaction(self._execute_query_tx, query, parameters)
            return result
    
    @staticmethod
    def _execute_query_tx(tx, query: str, parameters: Dict[str, Any]):
        """Transaction function for write queries."""
        result = tx.run(query, parameters)
        return [dict(record) for record in result]
    
    def create_constraints_and_indexes(self):
        """Create necessary constraints and indexes for the graph schema."""
        constraints_and_indexes = [
            # Constraints for uniqueness
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Law) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
            
            # Vector index for similarity search
            f"""CREATE VECTOR INDEX document_embeddings 
                FOR (n:Document) ON (n.embedding) 
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {Config.VECTOR_DIMENSION},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}""",
            
            # Regular indexes for performance
            "CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.source)",
            "CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.topic)",
            "CREATE INDEX IF NOT EXISTS FOR (a:Author) ON (a.name)",
        ]
        
        for query in constraints_and_indexes:
            try:
                self.execute_query(query)
                logger.info(f"Successfully executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to execute constraint/index: {e}")