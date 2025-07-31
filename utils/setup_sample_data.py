"""Utility to set up sample data in the RAG system."""
import logging
from core.rag_system_complete import CompleteRAGSystem
from data.sample_data import get_sample_data

logger = logging.getLogger(__name__)

def setup_sample_data():
    """Set up sample data in the RAG system."""
    logger.info("Setting up sample data...")
    
    # Initialize RAG system 
    rag_system = CompleteRAGSystem()
    
    try:
        # Get sample data
        sample_data = get_sample_data()
        
        # Store sample documents
        for doc_data in sample_data['documents']:
            text = doc_data['text']
            metadata = doc_data['metadata']
            
            doc_id = rag_system.store_document(text, metadata)
            logger.info(f"Stored document: {doc_id}")
        
        # Get and display statistics
        stats = rag_system.get_graph_statistics()
        logger.info(f"Graph statistics: {stats}")
        
        print("\n=== Sample Data Setup Complete ===")
        print(f"Documents stored: {stats.get('doc_count', 0)}")
        print(f"Authors: {stats.get('author_count', 0)}")
        print(f"Concepts: {stats.get('concept_count', 0)}")
        print(f"Laws: {stats.get('law_count', 0)}")
        print(f"Topics: {stats.get('topic_count', 0)}")
        
    except Exception as e:
        logger.error(f"Failed to setup sample data: {e}")
        raise
    finally:
        rag_system.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_sample_data()