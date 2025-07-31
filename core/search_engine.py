"""Search engine for vector similarity and hybrid graph-based retrieval."""
import logging
from typing import List, Dict, Any, Optional
from database.neo4j_client import Neo4jClient
from services.embedding_service import EmbeddingService
from config import Config

logger = logging.getLogger(__name__)

class SearchEngine:
    """Hybrid search engine combining vector similarity and graph relationships."""
    
    def __init__(self, db_client: Neo4jClient, embedding_service: EmbeddingService):
        """Initialize search engine with database and embedding services."""
        self.db_client = db_client
        self.embedding_service = embedding_service
    
    def vector_search(self, query: str, top_k: int = None, 
                     filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using Neo4j's vector index.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional filters for author, topic, source, etc.
            
        Returns:
            List of documents with similarity scores
        """
        if top_k is None:
            top_k = Config.TOP_K_RESULTS
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)
        
        # Build Cypher query for vector search
        base_query = """
        CALL db.index.vector.queryNodes('document_embeddings', $top_k, $query_embedding)
        YIELD node, score
        """
        
        # Add filters if provided
        where_clauses = []
        if filters:
            if filters.get('author'):
                where_clauses.append("EXISTS((a:Author {name: $author})-[:WROTE]->(node))")
            if filters.get('topic'):
                where_clauses.append("EXISTS((node)-[:RELATED_TO]->(t:Topic {name: $topic}))")
            if filters.get('source'):
                where_clauses.append("node.source = $source")
        
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        base_query += """
        RETURN node.id as id, node.text as text, node.source as source, 
               node.author as author, node.topic as topic, score
        ORDER BY score DESC
        """
        
        params = {
            'top_k': top_k,
            'query_embedding': query_embedding,
            **(filters if filters else {})
        }
        
        results = self.db_client.execute_query(base_query, params)
        logger.info(f"Vector search returned {len(results)} results")
        return results
    
    def graph_enhanced_search(self, query: str, top_k: int = None,
                            expand_relationships: bool = True) -> List[Dict[str, Any]]:
        """
        Perform graph-enhanced search that combines vector similarity 
        with graph relationship traversal.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            expand_relationships: Whether to include related documents
            
        Returns:
            Enhanced search results with relationship context
        """
        if top_k is None:
            top_k = Config.TOP_K_RESULTS
        
        # First, get vector search results
        vector_results = self.vector_search(query, top_k)
        
        if not expand_relationships:
            return vector_results
        
        # Enhance results with graph relationships
        enhanced_results = []
        
        for result in vector_results:
            doc_id = result['id']
            
            # Get related documents through graph relationships
            relationship_query = """
            MATCH (d:Document {id: $doc_id})
            OPTIONAL MATCH (d)-[:MENTIONS]->(c:Concept)<-[:MENTIONS]-(related1:Document)
            OPTIONAL MATCH (d)-[:CITES]->(l:Law)<-[:CITES]-(related2:Document)
            OPTIONAL MATCH (d)-[:RELATED_TO]->(t:Topic)<-[:RELATED_TO]-(related3:Document)
            OPTIONAL MATCH (a:Author)-[:WROTE]->(d)
            OPTIONAL MATCH (a)-[:WROTE]->(related4:Document)
            
            RETURN 
                collect(DISTINCT c.name) as concepts,
                collect(DISTINCT l.name) as laws,
                collect(DISTINCT t.name) as topics,
                a.name as author,
                collect(DISTINCT related1.id) + collect(DISTINCT related2.id) + 
                collect(DISTINCT related3.id) + collect(DISTINCT related4.id) as related_doc_ids
            """
            
            relationship_data = self.db_client.execute_query(
                relationship_query, {'doc_id': doc_id}
            )
            
            if relationship_data:
                rel_info = relationship_data[0]
                result.update({
                    'concepts': rel_info['concepts'],
                    'laws': rel_info['laws'],
                    'topics': rel_info['topics'],
                    'related_documents': [rid for rid in rel_info['related_doc_ids'] 
                                        if rid and rid != doc_id][:3]  # Limit to 3 related docs
                })
            
            enhanced_results.append(result)
        
        logger.info(f"Enhanced search completed for {len(enhanced_results)} results")
        return enhanced_results
    
    def search_by_author(self, author: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search documents by a specific author."""
        if top_k is None:
            top_k = Config.TOP_K_RESULTS
        
        query = """
        MATCH (a:Author {name: $author})-[:WROTE]->(d:Document)
        RETURN d.id as id, d.text as text, d.source as source, 
               d.author as author, d.topic as topic
        ORDER BY d.created_at DESC
        LIMIT $top_k
        """
        
        return self.db_client.execute_query(query, {'author': author, 'top_k': top_k})
    
    def search_by_concept(self, concept: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search documents that mention a specific concept."""
        if top_k is None:
            top_k = Config.TOP_K_RESULTS
        
        query = """
        MATCH (c:Concept {name: $concept})<-[:MENTIONS]-(d:Document)
        RETURN d.id as id, d.text as text, d.source as source, 
               d.author as author, d.topic as topic
        ORDER BY d.created_at DESC
        LIMIT $top_k
        """
        
        return self.db_client.execute_query(query, {'concept': concept, 'top_k': top_k})
    
    def search_by_law(self, law: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search documents that cite a specific law."""
        if top_k is None:
            top_k = Config.TOP_K_RESULTS
        
        query = """
        MATCH (l:Law {name: $law})<-[:CITES]-(d:Document)
        RETURN d.id as id, d.text as text, d.source as source, 
               d.author as author, d.topic as topic
        ORDER BY d.created_at DESC
        LIMIT $top_k
        """
        
        return self.db_client.execute_query(query, {'law': law, 'top_k': top_k})