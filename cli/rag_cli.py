"""Command-line interface for the RAG system."""
import click
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from core.rag_system_complete import CompleteRAGSystem
from utils.setup_sample_data import setup_sample_data
from config import Config
import json

console = Console()
logger = logging.getLogger(__name__)

class RAGInterface:
    """Interactive interface for the RAG system."""
    
    def __init__(self):
        """Initialize the RAG interface."""
        self.rag_system = None
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the RAG system with error handling."""
        try:
            Config.validate()
            self.rag_system = CompleteRAGSystem()
            console.print("✅ RAG system initialized successfully", style="green")
        except Exception as e:
            console.print(f"❌ Failed to initialize RAG system: {e}", style="red")
            raise
    
    def add_document(self, text: str, source: str, author: str, topic: str):
        """Add a document to the system."""
        try:
            metadata = {
                'source': source,
                'author': author, 
                'topic': topic
            }
            
            with console.status("Processing and storing document..."):
                doc_id = self.rag_system.store_document(text, metadata)
            
            console.print(f"✅ Document stored successfully with ID: {doc_id}", style="green")
            return doc_id
            
        except Exception as e:
            console.print(f"❌ Failed to store document: {e}", style="red")
            return None
    
    def search_documents(self, query: str, search_type: str = "hybrid", 
                        filters: dict = None, show_details: bool = True):
        """Search for documents and display results."""
        try:
            with console.status("Searching documents..."):
                results = self.rag_system.search(query, search_type, filters)
            
            if not results:
                console.print("No documents found matching your query.", style="yellow")
                return []
            
            # Display results in a table
            table = Table(title=f"Search Results for: '{query}' ({search_type} search)")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Text Preview", style="white", width=50)
            table.add_column("Author", style="green", width=15)
            table.add_column("Topic", style="blue", width=12)
            table.add_column("Score", style="magenta", width=8)
            
            for result in results[:10]:  # Show top 10 results
                text_preview = result['text'][:100] + "..." if len(result['text']) > 100 else result['text']
                score = f"{result.get('score', 0.0):.3f}" if result.get('score') else "N/A"
                
                table.add_row(
                    result['id'][:8],
                    text_preview,
                    result.get('author', 'Unknown'),
                    result.get('topic', 'General'),
                    score
                )
            
            console.print(table)
            
            if show_details and results:
                self._show_result_details(results[0])
            
            return results
            
        except Exception as e:
            console.print(f"❌ Search failed: {e}", style="red")
            return []
    
    def _show_result_details(self, result: dict):
        """Show detailed information about a search result."""
        details = []
        
        details.append(f"[bold]Document ID:[/bold] {result['id']}")
        details.append(f"[bold]Source:[/bold] {result.get('source', 'Unknown')}")
        details.append(f"[bold]Author:[/bold] {result.get('author', 'Unknown')}")
        details.append(f"[bold]Topic:[/bold] {result.get('topic', 'General')}")
        
        if 'score' in result:
            details.append(f"[bold]Similarity Score:[/bold] {result['score']:.4f}")
        
        if 'concepts' in result and result['concepts']:
            details.append(f"[bold]Concepts:[/bold] {', '.join(result['concepts'][:5])}")
        
        if 'laws' in result and result['laws']:
            details.append(f"[bold]Laws Referenced:[/bold] {', '.join(result['laws'])}")
        
        details.append(f"\n[bold]Full Text:[/bold]\n{result['text']}")
        
        panel = Panel("\n".join(details), title="Top Result Details", border_style="blue")
        console.print(panel)
    
    def ask_question(self, question: str, search_type: str = "hybrid", 
                    include_sources: bool = True):
        """Ask a question and get a RAG-generated response."""
        try:
            with console.status("Generating response..."):
                response_data = self.rag_system.rag_response(
                    question, search_type, include_sources=include_sources
                )
            
            # Display the response
            response_panel = Panel(
                response_data['response'],
                title=f"Response (Confidence: {response_data['confidence']:.2f})",
                border_style="green"
            )
            console.print(response_panel)
            
            # Display sources if included
            if include_sources and response_data.get('sources'):
                self._display_sources(response_data['sources'])
            
            return response_data
            
        except Exception as e:
            console.print(f"❌ Failed to generate response: {e}", style="red")
            return None
    
    def _display_sources(self, sources: list):
        """Display source documents used in the response."""
        console.print("\n[bold]Sources Used:[/bold]", style="blue")
        
        for i, source in enumerate(sources, 1):
            source_info = [
                f"[bold]{i}. Source:[/bold] {source.get('source', 'Unknown')}",
                f"[bold]Author:[/bold] {source.get('author', 'Unknown')}",
                f"[bold]Topic:[/bold] {source.get('topic', 'General')}",
            ]
            
            if 'score' in source:
                source_info.append(f"[bold]Score:[/bold] {source['score']:.3f}")
            
            if 'concepts' in source and source['concepts']:
                source_info.append(f"[bold]Concepts:[/bold] {', '.join(source['concepts'][:3])}")
            
            source_info.append(f"\n[italic]{source['text']}[/italic]")
            
            panel = Panel("\n".join(source_info), border_style="dim")
            console.print(panel)
    
    def show_statistics(self):
        """Display system statistics."""
        try:
            stats = self.rag_system.get_graph_statistics()
            
            stats_table = Table(title="Knowledge Graph Statistics")
            stats_table.add_column("Entity Type", style="cyan")
            stats_table.add_column("Count", style="green")
            
            for key, value in stats.items():
                entity_type = key.replace('_count', '').replace('_', ' ').title()
                stats_table.add_row(entity_type, str(value))
            
            console.print(stats_table)
            
        except Exception as e:
            console.print(f"❌ Failed to get statistics: {e}", style="red")
    
    def close(self):
        """Close the RAG system."""
        if self.rag_system:
            self.rag_system.close()

# CLI Commands
@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """Neo4j RAG System - Retrieval-Augmented Generation with Graph Database"""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

@cli.command()
def setup():
    """Set up sample data in the system"""
    try:
        setup_sample_data()
        console.print("✅ Sample data setup complete!", style="green")
    except Exception as e:
        console.print(f"❌ Setup failed: {e}", style="red")

@cli.command() 
@click.option('--text', prompt='Document text', help='The document text to store')
@click.option('--source', prompt='Source', help='Document source')
@click.option('--author', prompt='Author', help='Document author')
@click.option('--topic', prompt='Topic', help='Document topic')
def add(text, source, author, topic):
    """Add a document to the system"""
    interface = RAGInterface()
    try:
        interface.add_document(text, source, author, topic)
    finally:
        interface.close()

@cli.command()
@click.option('--query', prompt='Search query', help='Text to search for')
@click.option('--type', 'search_type', default='hybrid', 
              type=click.Choice(['vector', 'hybrid', 'author', 'concept', 'law']),
              help='Type of search to perform')
def search(query, search_type):
    """Search for documents"""
    interface = RAGInterface()
    try:
        interface.search_documents(query, search_type)
    finally:
        interface.close()

@cli.command()
@click.option('--question', prompt='Your question', help='Question to ask the system')
@click.option('--type', 'search_type', default='hybrid',
              type=click.Choice(['vector', 'hybrid', 'author', 'concept', 'law']),
              help='Type of search to use for retrieval')
def ask(question, search_type):
    """Ask a question and get a RAG response"""
    interface = RAGInterface()
    try:
        interface.ask_question(question, search_type)
    finally:
        interface.close()

@cli.command()
def stats():
    """Show system statistics"""
    interface = RAGInterface()
    try:
        interface.show_statistics()
    finally:
        interface.close()

@cli.command()
def interactive():
    """Start interactive mode"""
    interface = RAGInterface()
    
    try:
        console.print(Panel("Welcome to Neo4j RAG System Interactive Mode", style="bold blue"))
        console.print("Commands: add, search, ask, stats, help, quit")
        
        while True:
            try:
                command = console.input("\n[bold cyan]rag>[/bold cyan] ").strip().lower()
                
                if command == 'quit' or command == 'exit':
                    break
                elif command == 'help':
                    console.print("""
Available commands:
- add: Add a new document
- search <query>: Search for documents  
- ask <question>: Ask a question
- stats: Show system statistics
- quit: Exit interactive mode
                    """)
                elif command == 'stats':
                    interface.show_statistics()
                elif command.startswith('search '):
                    query = command[7:]
                    interface.search_documents(query)
                elif command.startswith('ask '):
                    question = command[4:]
                    interface.ask_question(question)
                elif command == 'add':
                    text = console.input("Document text: ")
                    source = console.input("Source: ")
                    author = console.input("Author: ")
                    topic = console.input("Topic: ")
                    interface.add_document(text, source, author, topic)
                else:
                    console.print("Unknown command. Type 'help' for available commands.", style="yellow")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"❌ Error: {e}", style="red")
        
        console.print("Goodbye! 👋", style="green")
        
    finally:
        interface.close()

if __name__ == '__main__':
    cli()