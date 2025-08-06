"""Test script for the Dell document processor using real extracted text."""
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from services.dell_document_processor_v2 import DellDocumentProcessor

def test_dell_processor():
    """Test the Dell document processor with real extracted text."""
    print("🚀 Testing Dell Document Processor v2...")
    
    # Read the extracted Dell manual text
    text_file = project_root / "data" / "dell-pro-max-14-ma14250-owners-manual-en-us.txt"
    
    if not text_file.exists():
        print(f"❌ Text file not found: {text_file}")
        return
    
    print(f"📖 Reading text from: {text_file}")
    with open(text_file, 'r', encoding='utf-8') as f:
        extracted_text = f.read()
    
    print(f"📊 Original text length: {len(extracted_text):,} characters")
    
    # Initialize the processor
    processor = DellDocumentProcessor(
        chunk_size=1500,  # Larger chunks for technical content
        chunk_overlap=400  # More overlap for context preservation
    )
    
    # Process the document
    print("🔄 Processing document...")
    result = processor.process_dell_document(
        extracted_text,
        source_metadata={
            'source_file': 'dell-pro-max-14-ma14250-owners-manual-en-us.pdf',
            'extraction_method': 'pdf_text_extraction'
        }
    )
    
    # Print summary
    print("\n" + "="*60)
    print("📄 DELL DOCUMENT PROCESSING RESULTS")
    print("="*60)
    
    print(f"✅ Processing completed successfully")
    print(f"📊 Total chunks created: {result['chunk_count']}")
    print(f"📏 Average chunk size: {result['processing_summary']['avg_chunk_size']} characters")
    print(f"🏷️  Entity types found: {result['processing_summary']['entity_types_found']}")
    print(f"🔢 Total entities extracted: {result['processing_summary']['total_entities']}")
    
    # Document metadata
    metadata = result['metadata']
    print(f"\n📋 Document Information:")
    if metadata.get('document_title'):
        print(f"   Title: {metadata['document_title']}")
    if metadata.get('model_number'):
        print(f"   Model: {metadata['model_number']}")
    if metadata.get('revision'):
        print(f"   Revision: {metadata['revision']}")
    if metadata.get('publication_date'):
        print(f"   Date: {metadata['publication_date']}")
    
    # Content statistics
    content_stats = metadata.get('content_stats', {})
    if content_stats:
        print(f"\n📈 Content Analysis:")
        for stat_name, count in content_stats.items():
            if count > 0:
                print(f"   {stat_name.replace('_', ' ').title()}: {count}")
    
    # Chunk type distribution
    chunk_dist = result.get('chunk_type_distribution', {})
    if chunk_dist:
        print(f"\n🧩 Chunk Type Distribution:")
        for chunk_type, count in sorted(chunk_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"   {chunk_type.replace('_', ' ').title()}: {count} chunks")
    
    # Entity extraction summary
    entities = result.get('entities', {})
    if entities:
        print(f"\n🏷️  Extracted Entities:")
        for entity_type, entity_list in entities.items():
            if entity_list:
                print(f"   {entity_type.replace('_', ' ').title()}: {len(entity_list)} found")
                # Show first few examples
                examples = entity_list[:3]
                if examples:
                    print(f"      Examples: {', '.join(examples)}")
    
    # Show sample chunks
    chunks = result.get('chunks', [])
    if chunks:
        print(f"\n📝 Sample Chunks:")
        
        # Show different types of chunks
        chunk_types_shown = set()
        for i, chunk in enumerate(chunks[:10]):  # Show first 10 chunks
            chunk_type = chunk.get('chunk_type', 'unknown')
            if chunk_type not in chunk_types_shown:
                print(f"\n--- {chunk_type.replace('_', ' ').title()} (Chunk {i+1}) ---")
                print(f"ID: {chunk['id']}")
                print(f"Text preview: {chunk['text'][:200]}...")
                if chunk.get('entities'):
                    entity_summary = {k: len(v) for k, v in chunk['entities'].items() if v}
                    if entity_summary:
                        print(f"Entities: {entity_summary}")
                chunk_types_shown.add(chunk_type)
                
                if len(chunk_types_shown) >= 3:  # Show max 3 different types
                    break
    
    # Save results
    output_file = f"dell_processed_results_{int(__import__('time').time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full results saved to: {output_file}")
    print("="*60)
    
    return result

if __name__ == "__main__":
    test_dell_processor()
