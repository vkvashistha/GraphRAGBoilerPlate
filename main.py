"""Main entry point for the Neo4j RAG System."""
import logging
from cli.rag_cli import cli

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    cli()