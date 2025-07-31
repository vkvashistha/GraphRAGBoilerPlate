"""Complete RAG system with search and generation capabilities."""
import logging
from typing import List, Dict, Any, Optional
from core.rag_system import RAGSystem
from core.search_engine import SearchEngine
from config import Config
import openai

logger = logging.getLogger(__name__)

class CompleteRAGSystem(RAGSystem):
    """Complete RAG system extending base with search and generation capabilities."""
    
    def __init__(self):
        """Initialize the complete RAG system."""
        super().__init__()
        self.search_engine = SearchEngine(self.db_client, self.embedding_service)
    
    def search(self, query: str, search_type: str = "hybrid", 
              filters: Dict[str, Any] = None, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using various strategies.
        
        Args:
            query: Search query
            search_type: Type of search ("vector", "hybrid", "author", "concept", "law")
            filters: Optional filters
            top_k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if top_k is None:
            top_k = Config.TOP_K_RESULTS
        
        if search_type == "vector":
            return self.search_engine.vector_search(query, top_k, filters)
        elif search_type == "hybrid":
            return self.search_engine.graph_enhanced_search(query, top_k)
        elif search_type == "author":
            author = filters.get('author') if filters else query
            return self.search_engine.search_by_author(author, top_k)
        elif search_type == "concept":
            concept = filters.get('concept') if filters else query
            return self.search_engine.search_by_concept(concept, top_k)
        elif search_type == "law":
            law = filters.get('law') if filters else query
            return self.search_engine.search_by_law(law, top_k)
        else:
            raise ValueError(f"Unknown search type: {search_type}")
    
    def rag_response(self, query: str, search_type: str = "hybrid", 
                    filters: Dict[str, Any] = None, 
                    include_sources: bool = True) -> Dict[str, Any]:
        """
        Generate a response using retrieved documents and GPT-4.
        
        Args:
            query: User query
            search_type: Type of search to use for retrieval
            filters: Optional search filters
            include_sources: Whether to include source documents in response
            
        Returns:
            Dictionary containing response and metadata
        """
        logger.info(f"Generating RAG response for query: {query[:100]}...")
        
        # Retrieve relevant documents
        retrieved_docs = self.search(query, search_type, filters)
        
        if not retrieved_docs:
            return {
                'response': "I couldn't find any relevant documents to answer your question.",
                'sources': [],
                'confidence': 0.0
            }
        
        # Prepare context from retrieved documents
        context_parts = []
        sources = []
        
        for i, doc in enumerate(retrieved_docs[:Config.TOP_K_RESULTS]):
            context_parts.append(f"Document {i+1}:\n{doc['text']}")
            
            source_info = {
                'id': doc['id'],
                'text': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text'],
                'source': doc.get('source', 'unknown'),
                'author': doc.get('author', 'unknown'),
                'topic': doc.get('topic', 'general'),
                'score': doc.get('score', 0.0)
            }
            
            # Add relationship context if available
            if 'concepts' in doc:
                source_info['concepts'] = doc['concepts']
            if 'laws' in doc:
                source_info['laws'] = doc['laws']
            
            sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        # Generate response using GPT-4
        response_text = self._generate_response(query, context)
        
        # Calculate confidence based on similarity scores
        avg_score = sum(doc.get('score', 0.0) for doc in retrieved_docs) / len(retrieved_docs)
        confidence = min(avg_score * 1.2, 1.0)  # Scale and cap at 1.0
        
        result = {
            'response': response_text,
            'confidence': confidence,
            'num_sources': len(sources)
        }
        
        if include_sources:
            result['sources'] = sources
        
        logger.info(f"Generated response with {len(sources)} sources, confidence: {confidence:.2f}")
        return result
    
    def _generate_response(self, query: str, context: str) -> str:
        """Generate response using OpenAI GPT-4 with retrieved context."""
        
        system_prompt = """You are a helpful AI assistant that answers questions based on provided documents. 
        
        Instructions:
        1. Use only the information provided in the context documents to answer questions
        2. If the context doesn't contain enough information, say so clearly
        3. Cite specific parts of the documents when making claims
        4. Be concise but comprehensive in your answers
        5. If you find contradictions in the documents, point them out
        6. When discussing legal matters, always recommend consulting with a qualified professional
        """
        
        user_prompt = f"""Based on the following documents, please answer this question: {query}

        Context Documents:
        {context}
        
        Please provide a clear, well-structured answer based solely on the information in these documents."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"I encountered an error while generating the response: {str(e)}"
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        stats_query = """
        MATCH (d:Document) WITH count(d) as doc_count
        MATCH (a:Author) WITH doc_count, count(a) as author_count  
        MATCH (c:Concept) WITH doc_count, author_count, count(c) as concept_count
        MATCH (l:Law) WITH doc_count, author_count, concept_count, count(l) as law_count
        MATCH (t:Topic) WITH doc_count, author_count, concept_count, law_count, count(t) as topic_count
        RETURN doc_count, author_count, concept_count, law_count, topic_count
        """
        
        result = self.db_client.execute_query(stats_query)
        if result:
            return result[0]
        return {}
    
    def close(self):
        """Close all connections."""
        self.db_client.close()