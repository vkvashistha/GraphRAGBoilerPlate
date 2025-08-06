"""Integration script to add processed Dell documents to Neo4j database."""
import sys
from pathlib import Path
import logging
import time

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from services.dell_document_processor_v2 import DellDocumentProcessor
from core.rag_system_complete import CompleteRAGSystem
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_dell_document_to_neo4j():
    """Process Dell document and integrate it into Neo4j database."""
    print("🚀 Starting Dell Document Integration to Neo4j...")
    
    # Read the extracted Dell manual text
    text_file = project_root / "data" / "dell-pro-max-14-ma14250-owners-manual-en-us.txt"
    
    if not text_file.exists():
        print(f"❌ Text file not found: {text_file}")
        return False
    
    print(f"📖 Reading Dell manual from: {text_file}")
    with open(text_file, 'r', encoding='utf-8') as f:
        extracted_text = f.read()
    
    print(f"📊 Original text length: {len(extracted_text):,} characters")
    
    # Initialize the Dell document processor
    print("🔧 Initializing Dell document processor...")
    processor = DellDocumentProcessor(
        chunk_size=1500,  # Optimized for technical content
        chunk_overlap=400
    )
    
    # Process the document
    print("🔄 Processing Dell document...")
    processed_result = processor.process_dell_document(
        extracted_text,
        source_metadata={
            'source_file': 'dell-pro-max-14-ma14250-owners-manual-en-us.pdf',
            'extraction_method': 'pdf_text_extraction',
            'document_category': 'technical_manual',
            'manufacturer': 'Dell',
            'product_line': 'Pro Max'
        }
    )
    
    print(f"✅ Document processed into {processed_result['chunk_count']} chunks")
    
    # Initialize RAG system
    print("🔧 Initializing RAG system...")
    rag_system = CompleteRAGSystem()
    
    # Store each chunk in Neo4j
    print("💾 Storing chunks in Neo4j...")
    stored_count = 0
    
    for chunk in processed_result['chunks']:
        try:
            # Prepare document data for Neo4j storage
            document_data = {
                'text': chunk['text'],
                'source': processed_result['metadata'].get('source_file', 'dell_manual'),
                'author': 'Dell Technologies',  # Dell is the author
                'topic': 'technical_documentation',
                'chunk_id': chunk['id'],
                'chunk_index': chunk['chunk_index'],
                'chunk_type': chunk.get('chunk_type', 'general_content'),
                'document_type': 'dell_technical_manual',
                'model_number': processed_result['metadata'].get('model_number', 'MA14250'),
                'document_title': processed_result['metadata'].get('document_title', 'Dell Pro Max 14 Premium Manual')
            }
            
            # Extract entities for relationships
            entities = chunk.get('entities', {})
            
            # Store document in Neo4j (fixed method call)
            doc_id = rag_system.store_document(
                text=document_data['text'],
                metadata=document_data
            )
            
            # Create Dell-specific relationships
            create_dell_relationships(rag_system, doc_id, entities, processed_result['metadata'])
            
            stored_count += 1
            
            if stored_count % 10 == 0:
                print(f"   Stored {stored_count}/{processed_result['chunk_count']} chunks...")
                
        except Exception as e:
            logger.error(f"Error storing chunk {chunk['id']}: {e}")
            continue
    
    print(f"✅ Successfully stored {stored_count} chunks in Neo4j")
    
    # Create summary statistics
    print("\n📊 Integration Summary:")
    print(f"   Total chunks processed: {processed_result['chunk_count']}")
    print(f"   Chunks stored in Neo4j: {stored_count}")
    print(f"   Document type: {processed_result['metadata'].get('document_type', 'N/A')}")
    print(f"   Model: {processed_result['metadata'].get('model_number', 'N/A')}")
    
    # Show entity statistics
    entities = processed_result.get('entities', {})
    entity_counts = {k: len(v) for k, v in entities.items() if v}
    if entity_counts:
        print(f"   Entities extracted: {sum(entity_counts.values())} total")
        for entity_type, count in entity_counts.items():
            print(f"     {entity_type.replace('_', ' ').title()}: {count}")
    
    # Test the integration with a sample query
    print("\n🔍 Testing integration with sample queries...")
    test_queries = [
        "What are the specifications of the Dell Pro Max 14?",
        "How do I remove the battery?",
        "What ports are available on this laptop?",
        "What are the safety warnings for working inside the computer?"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        try:
            response = rag_system.rag_response(
                query=query,
                search_type="hybrid",
                filters={'topic': 'technical_documentation'}
            )
            print(f"✅ Response generated (confidence: {response['confidence']:.2f})")
            print(f"   Sources: {response['num_sources']} documents")
            print(f"   Preview: {response['response'][:150]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Close connections
    rag_system.close()
    
    print("\n🎉 Dell document integration completed successfully!")
    print("You can now ask questions about Dell technical documentation using the RAG system.")
    
    return True

def create_dell_relationships(rag_system, doc_id: str, entities: dict, metadata: dict):
    """Create Dell-specific relationships in Neo4j."""
    
    # Create relationships for Dell-specific entities
    try:
        # Model relationships
        model_numbers = entities.get('model_numbers', [])
        for model in model_numbers:
            create_model_relationship(rag_system, doc_id, model)
        
        # Component relationships
        components = entities.get('components', [])
        for component in components:
            create_component_relationship(rag_system, doc_id, component)
        
        # Port/Connector relationships
        ports = entities.get('ports_connectors', [])
        for port in ports:
            create_port_relationship(rag_system, doc_id, port)
        
        # Specification relationships
        specs = entities.get('specifications', [])
        for spec in specs:
            create_specification_relationship(rag_system, doc_id, spec)
        
        # Procedure relationships (for installation/removal procedures)
        procedures = entities.get('procedures', [])
        for procedure in procedures:
            create_procedure_relationship(rag_system, doc_id, procedure)
            
    except Exception as e:
        logger.error(f"Error creating Dell relationships for doc {doc_id}: {e}")

def create_model_relationship(rag_system, doc_id: str, model: str):
    """Create relationship between document and Dell model."""
    query = """
    MATCH (d:Document {id: $doc_id})
    MERGE (m:DellModel {name: $model})
    MERGE (d)-[:DESCRIBES]->(m)
    """
    rag_system.db_client.execute_write_query(query, {'doc_id': doc_id, 'model': model})

def create_component_relationship(rag_system, doc_id: str, component: str):
    """Create relationship between document and hardware component."""
    query = """
    MATCH (d:Document {id: $doc_id})
    MERGE (c:Component {name: $component})
    MERGE (d)-[:MENTIONS]->(c)
    """
    rag_system.db_client.execute_write_query(query, {'doc_id': doc_id, 'component': component})

def create_port_relationship(rag_system, doc_id: str, port: str):
    """Create relationship between document and port/connector."""
    query = """
    MATCH (d:Document {id: $doc_id})
    MERGE (p:Port {name: $port})
    MERGE (d)-[:DESCRIBES]->(p)
    """
    rag_system.db_client.execute_write_query(query, {'doc_id': doc_id, 'port': port})

def create_specification_relationship(rag_system, doc_id: str, spec: str):
    """Create relationship between document and specification."""
    query = """
    MATCH (d:Document {id: $doc_id})
    MERGE (s:Specification {value: $spec})
    MERGE (d)-[:SPECIFIES]->(s)
    """
    rag_system.db_client.execute_write_query(query, {'doc_id': doc_id, 'spec': spec})

def create_procedure_relationship(rag_system, doc_id: str, procedure: str):
    """Create relationship between document and procedure."""
    query = """
    MATCH (d:Document {id: $doc_id})
    MERGE (p:Procedure {name: $procedure})
    MERGE (d)-[:CONTAINS]->(p)
    """
    rag_system.db_client.execute_write_query(query, {'doc_id': doc_id, 'procedure': procedure})

if __name__ == "__main__":
    integrate_dell_document_to_neo4j()