"""Test script for Dell document queries after Neo4j integration."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from core.rag_system_complete import CompleteRAGSystem

def test_dell_queries():
    """Test Dell document queries using the RAG system."""
    print("🔍 Testing Dell Document Queries...")
    
    # Initialize RAG system
    rag_system = CompleteRAGSystem()
    
    # Test queries for Dell technical documentation
    test_queries = [
        "What are the specifications of the Dell Pro Max 14?",
        "How do I remove the battery?",
        "What ports are available on this laptop?",
        "What are the safety warnings for working inside the computer?"
    ]
    
    print(f"Running {len(test_queries)} test queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"{'='*60}")
        print(f"Query {i}/{len(test_queries)}: {query}")
        print(f"{'='*60}")
        
        try:
            response = rag_system.rag_response(
                query=query,
                search_type="hybrid",
                filters={'topic': 'technical_documentation'}
            )
            
            print(f"✅ Response generated successfully")
            print(f"   Confidence: {response['confidence']:.2f}")
            print(f"   Sources: {response['num_sources']} documents")
            print(f"   Search results: {len(response.get('search_results', []))} chunks")
            print(f"\n📝 Response:")
            print(f"{response['response']}")
            
            # Show source information if available
            if 'search_results' in response and response['search_results']:
                print(f"\n📚 Top Sources:")
                for j, result in enumerate(response['search_results'][:3], 1):
                    chunk_type = result.get('chunk_type', 'general_content')
                    similarity = result.get('similarity_score', 0)
                    print(f"   {j}. Type: {chunk_type}, Similarity: {similarity:.3f}")
                    print(f"      Preview: {result['text'][:100]}...")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        print("\n")
    
    # Close connections
    rag_system.close()
    
    print("🎉 Dell query testing completed!")

def test_additional_queries():
    """Test additional Dell-specific queries."""
    print("\n🔍 Testing Additional Dell Queries...")
    
    # Initialize RAG system
    rag_system = CompleteRAGSystem()
    
    # Additional test queries
    additional_queries = [
        "What is the model number of this Dell laptop?",
        "How do I access the BIOS settings?",
        "What are the memory specifications?",
        "How do I install or remove components?",
        "What regulatory information is provided?",
        "What are the display specifications?",
        "How do I connect external devices?",
        "What troubleshooting steps are available?"
    ]
    
    print(f"Running {len(additional_queries)} additional queries...\n")
    
    for i, query in enumerate(additional_queries, 1):
        print(f"Query {i}: {query}")
        
        try:
            response = rag_system.rag_response(
                query=query,
                search_type="hybrid",
                filters={'document_type': 'dell_technical_manual'}
            )
            
            print(f"   ✅ Confidence: {response['confidence']:.2f}, Sources: {response['num_sources']}")
            print(f"   Preview: {response['response'][:120]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Close connections
    rag_system.close()

if __name__ == "__main__":
    test_dell_queries()
    test_additional_queries()
