# Neo4j RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system using Neo4j as the primary backend for both vector and graph-based storage and retrieval.

## Features

- **Hybrid Search**: Combines vector similarity search with graph relationship traversal
- **Vector Embeddings**: Uses OpenAI's text-embedding-ada-002 for semantic understanding
- **Graph Relationships**: Rich knowledge graph with Authors, Documents, Concepts, Laws, and Topics
- **RAG Generation**: GPT-4 powered responses using retrieved context
- **Modular Architecture**: Clean separation of concerns with extensible design
- **CLI Interface**: Interactive command-line interface for easy interaction

## Graph Schema

```
(:Author)-[:WROTE]->(:Document)
(:Document)-[:MENTIONS]->(:Concept)
(:Document)-[:CITES]->(:Law)
(:Document)-[:RELATED_TO]->(:Topic)
```

## Installation

1. **Prerequisites**:
   - Neo4j Database (v5.0+)
   - Python 3.8+
   - OpenAI API Key

2. **Neo4j Setup**:
   ```bash
   # Install Neo4j Desktop or use Neo4j AuraDB
   # Create a new database with default credentials
   # Note down your connection details
   ```

3. **Python Environment**:
   ```bash
   # Clone this repository
   git clone <repository-url>
   cd neo4j-rag-system
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Configuration**:
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your credentials
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_neo4j_password
   OPENAI_API_KEY=your_openai_api_key
   ```

## Quick Start

1. **Setup Sample Data**:
   ```bash
   python -m cli.rag_cli setup
   ```

2. **Interactive Mode**:
   ```bash
   python -m cli.rag_cli interactive
   ```

3. **Command-Line Usage**:
   ```bash
   # Ask a question
   python -m cli.rag_cli ask --question "What are the key privacy rights under GDPR?"
   
   # Search documents
   python -m cli.rag_cli search --query "constitutional rights" --type hybrid
   
   # Add a document
   python -m cli.rag_cli add --text "Your document text" --source "Source Name" --author "Author Name" --topic "Topic"
   
   # View statistics
   python -m cli.rag_cli stats
   ```

## Core Components

### 1. Document Storage (`store_document`)
- Splits documents into semantic chunks
- Generates vector embeddings using OpenAI
- Stores in Neo4j with rich metadata
- Creates graph relationships automatically

### 2. Hybrid Search (`search`)
- **Vector Search**: Cosine similarity using Neo4j's vector index
- **Hybrid Search**: Combines vector similarity with graph relationships
- **Filtered Search**: Search by author, concept, law, or topic
- **Graph Enhancement**: Expands results using relationship traversal

### 3. RAG Response (`rag_response`)
- Retrieves relevant documents
- Constructs context for GPT-4
- Generates coherent responses
- Includes source attribution and confidence scoring

## Search Types

1. **Vector Search**: Pure semantic similarity
2. **Hybrid Search**: Vector + graph relationships (recommended)
3. **Author Search**: Documents by specific author
4. **Concept Search**: Documents mentioning specific concepts
5. **Law Search**: Documents citing specific laws

## Architecture

```
├── config.py              # Configuration management
├── database/
│   └── neo4j_client.py    # Neo4j connection and queries
├── services/
│   ├── embedding_service.py    # OpenAI embeddings
│   └── document_processor.py   # Text processing and chunking
├── core/
│   ├── rag_system.py          # Core RAG implementation
│   ├── search_engine.py       # Search functionality
│   └── rag_system_complete.py # Complete system with generation
├── data/
│   └── sample_data.py         # Sample data for testing
├── utils/
│   └── setup_sample_data.py   # Data setup utilities
└── cli/
    └── rag_cli.py            # Command-line interface
```

## Key Features Explained

### Vector Search with Neo4j
Neo4j's native vector index enables efficient cosine similarity search:
```cypher
CALL db.index.vector.queryNodes('document_embeddings', $top_k, $query_embedding)
YIELD node, score
```

### Graph-Enhanced Retrieval
Expands search results using graph relationships:
```cypher
MATCH (d:Document {id: $doc_id})
OPTIONAL MATCH (d)-[:MENTIONS]->(c:Concept)<-[:MENTIONS]-(related:Document)
```

### Hybrid Search Strategy
1. Perform vector similarity search
2. For each result, find related documents through graph traversal
3. Enrich results with relationship context
4. Return comprehensive results with semantic and structural relevance

## Extending the System

### Adding New Node Types
To add new entities (e.g., Court, Case):

1. **Update Graph Schema**:
   ```python
   # In neo4j_client.py, add new constraints
   "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Court) REQUIRE c.name IS UNIQUE"
   ```

2. **Add Relationship Creation**:
   ```python
   # In rag_system.py
   def _create_court_relationship(self, doc_id: str, court: str):
       query = """
       MATCH (d:Document {id: $doc_id})
       MERGE (c:Court {name: $court})
       MERGE (d)-[:HEARD_IN]->(c)
       """
       self.db_client.execute_write_query(query, {'doc_id': doc_id, 'court': court})
   ```

3. **Update Entity Extraction**:
   ```python
   # In document_processor.py
   def extract_entities(self, text: str):
       # Add court extraction logic
       court_pattern = r'\b[A-Z][a-z]+\s+Court\b'
       courts = re.findall(court_pattern, text)
       entities['courts'] = courts
   ```

### Performance Optimization

1. **Indexing**: Create indexes on frequently queried properties
2. **Batch Processing**: Process multiple documents in transactions
3. **Caching**: Cache embeddings for frequently accessed content
4. **Connection Pooling**: Use connection pooling for high-throughput scenarios

### Production Considerations

1. **Error Handling**: Comprehensive error handling and logging
2. **Monitoring**: Track system performance and query statistics
3. **Security**: Secure API keys and database credentials
4. **Scaling**: Consider Neo4j clustering for large deployments
5. **Backup**: Regular database backups and disaster recovery

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Verify Neo4j is running
   - Check connection credentials in `.env`
   - Ensure network connectivity

2. **OpenAI API Errors**:
   - Verify API key is valid
   - Check API quotas and limits
   - Monitor rate limiting

3. **Performance Issues**:
   - Check vector index creation
   - Monitor query performance
   - Consider reducing chunk sizes

### Getting Help

- Check logs for detailed error messages
- Use debug mode: `--debug` flag
- Review Neo4j query profiling
- Monitor system resources

## License

MIT License - see LICENSE file for details.