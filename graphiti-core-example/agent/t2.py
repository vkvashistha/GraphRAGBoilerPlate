from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from dotenv import load_dotenv
import os
import asyncio
from typing_extensions import TypedDict
from typing import Annotated
import uuid
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_EPISODE_MENTIONS
from graphiti_core.nodes import EpisodeType
from datetime import datetime, timezone
from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import ToolMessage

# Load environment variables from .env file
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

if not neo4j_uri or not neo4j_user or not neo4j_password:
    raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')

client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

def edges_to_facts_string(entities: list[EntityEdge]) -> str:
    return '-' + '\n- '.join([edge.fact for edge in entities])

@tool
async def get_dell_data(query: str) -> str:
    """Search the graphiti graph for information about Dell Pro Max 14 Premium laptop"""
    edge_results = await client.search(
        query,
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

class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str
    user_node_uuid: str

async def chatbot(state: State):
    facts_string = None
    if state['messages']:
        last_message = state['messages'][-1]
        graphiti_query = f'{"SalesBot" if isinstance(last_message, AIMessage) else state["user_name"]}: {last_message.content}'
        edge_results = await client.search(
            graphiti_query,
            num_results=5
        )
        facts_string = edges_to_facts_string(edge_results)

    system_message = SystemMessage(
        content=f"""You are a helpful, friendly assistant that answers user questions clearly and concisely.

Review any prior context below to make your answer more useful.

Conversation context:
{facts_string or 'No prior conversation history'}
"""
    )

    messages = [system_message] + state['messages']
    response = await llm.ainvoke(messages)

    # Add episode to Graphiti for future context
    asyncio.create_task(
        client.add_episode(
            name='Chatbot Response',
            episode_body=f'{state["user_name"]}: {state["messages"][-1]}\nBot: {response.content}',
            source=EpisodeType.message,
            reference_time=datetime.now(timezone.utc),
            source_description='Chatbot',
        )
    )

    return {'messages': [response]}

graph_builder = StateGraph(State)
graph_builder.add_node('agent', chatbot)
# ... any other nodes or routes ...

# Compile without a custom checkpointer
graph = graph_builder.compile()
print(graph)

async def main():
    user_name = 'jess'
    # record initial user context
    await client.add_episode(
        name='User Creation',
        episode_body=f'{user_name} is interested in buying a Dell Pro Max 14 Premium laptop',
        source=EpisodeType.text,
        reference_time=datetime.now(timezone.utc),
        source_description='Dell Support Agent',
    )

    # retrieve Jess’s node UUID for both search context and as thread_id
    nl = await client._search(user_name, NODE_HYBRID_SEARCH_EPISODE_MENTIONS)
    user_node_uuid = nl.nodes[0].uuid
    print(f"Using thread_id = user_node_uuid = {user_node_uuid}")

    # First invocation: ask a question
    ai_result = await graph.ainvoke(
        {
            'messages': [
                HumanMessage(content='Dell Pro Max 14 battery specifications')
            ],
            'user_name': user_name,
            'user_node_uuid': user_node_uuid,
        },
        config={'configurable': {'thread_id': user_node_uuid}}
    )

    msgs = ai_result['messages']
    question = next(m for m in msgs if isinstance(m, HumanMessage)).content
    response = list(m for m in msgs if isinstance(m, AIMessage))[-1].content
    search_results = next((m.content for m in msgs if isinstance(m, ToolMessage)), None)

    print(f"\nQuestion:\n{question}\n")
    print(f"Answer:\n{response}\n")
    if search_results:
        print(f"Search Results:\n{search_results}\n")

    await client.driver.close()

if __name__ == "__main__":
    asyncio.run(main())
