from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables from .env file
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

if not neo4j_uri or not neo4j_user or not neo4j_password:
    raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')

client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

def edges_to_facts_string(entities: list[EntityEdge]):
    return '-' + '\n- '.join([edge.fact for edge in entities])

@tool
async def get_dell_data(query: str) -> str:
    """Search the graphiti graph for information about Dell Pro Max 14 Premium laptop"""
    edge_results = await client.search(
        query,
        # You can uncomment and use this if you have the dell_device_node_uuid
        # center_node_uuid=dell_device_node_uuid,
        num_results=10,
    )
    return edges_to_facts_string(edge_results)


tools = [get_dell_data]
tool_node = ToolNode(tools)

# Get OpenAI API key from environment
openai_api_key = os.environ.get('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError('OPENAI_API_KEY must be set in the .env file')

# Initialize the LLM with the API key
llm = ChatOpenAI(
    model='gpt-4.1-mini',
    temperature=0,
    openai_api_key=openai_api_key
).bind_tools(tools)

async def main():

    # Test the tool node
    d = await tool_node.ainvoke({'messages': [await llm.ainvoke('Dell Pro Max 14 battery specifications')]})
    print(d)


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())