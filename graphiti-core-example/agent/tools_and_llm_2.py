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
from typing_extensions import TypedDict
from typing import Annotated
import uuid
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_EPISODE_MENTIONS
from graphiti_core.nodes import EpisodeType
from datetime import datetime, timezone
# from langchain.schema import HumanMessage, AIMessage, ToolMessage
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

def edges_to_facts_string(entities: list[EntityEdge]):
    return '-' + '\n- '.join([edge.fact for edge in entities])

async def get_user_chat_history(client: Graphiti, user_name: str, user_node_uuid: str = None) -> str:
    """Retrieve user's past questions and conversation history from Graphiti"""
    # Search for past user interactions and questions
    history_query = f'{user_name} asked question Dell laptop specifications battery performance'
    
    edge_results = await client.search(
        history_query,
        center_node_uuid=user_node_uuid if user_node_uuid else None,
        num_results=10  # Get more history for better context
    )
    
    if edge_results:
        return edges_to_facts_string(edge_results)
    else:
        return 'No previous conversation history found'

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

# async def main():
    
#     # Test the tool node
#     d = await tool_node.ainvoke({'messages': [await llm.ainvoke('Dell Pro Max 14 battery specifications')]})
#     print(d)

class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str
    user_node_uuid: str


async def chatbot(state: State):
    facts_string = None
    if len(state['messages']) > 0:
        last_message = state['messages'][-1]
        
        # Get comprehensive chat history for the user
        facts_string = await get_user_chat_history(
            client, 
            state['user_name'], 
            state.get('user_node_uuid')
        )

    # system_message = SystemMessage(
    #     content=f"""You are a skillfull shoe salesperson working for ManyBirds. Review information about the user and their prior conversation below and respond accordingly.
    #     Keep responses short and concise. And remember, always be selling (and helpful!)

    #     Things you'll need to know about the user in order to close a sale:
    #         - the user's shoe size
    #     - any other shoe needs? maybe for wide feet?
    #     - the user's preferred colors and styles
    #     - their budget

    #     Ensure that you ask the user for the above if you don't already know.

    #     Facts about the user and their conversation:
    #     {facts_string or 'No facts about the user and their conversation'}"""
    # )

    system_message = SystemMessage(
        content=f"""You are a helpful, friendly assistant that answers user questions clearly and concisely.  

            Review the user's past questions and conversation history below to provide more contextual and helpful answers.
            If the user has asked similar questions before, you can reference that context.
            If this relates to previous conversations, acknowledge the continuity.

            User's conversation history:
            {facts_string or 'No prior conversation history'}
            """
        )

    messages = [system_message] + state['messages']

    response = await llm.ainvoke(messages)

    # add the response to the graphiti graph.
    # this will allow us to use the graphiti search later in the conversation
    # we're doing async here to avoid blocking the graph execution
    
    # Store user question separately for better history tracking
    if len(state['messages']) > 0:
        last_message = state['messages'][-1]
        if isinstance(last_message, HumanMessage):
            asyncio.create_task(
                client.add_episode(
                    name='User Question',
                    episode_body=f'{state["user_name"]} asked: {last_message.content}',
                    source=EpisodeType.message,
                    reference_time=datetime.now(timezone.utc),
                    source_description='User Chat History',
                )
            )
    
    # Store the full conversation exchange
    asyncio.create_task(
        client.add_episode(
            name='Chatbot Response',
            episode_body=f'{state["user_name"]}: {state["messages"][-1].content if hasattr(state["messages"][-1], "content") else str(state["messages"][-1])}\nBot: {response.content}',
            source=EpisodeType.message,
            reference_time=datetime.now(timezone.utc),
            source_description='Chatbot Conversation',
        )
    )

    return {'messages': [response]}


graph_builder = StateGraph(State)

# memory = MemorySaver()


# Define the function that determines whether to continue or not
async def should_continue(state, config):
    messages = state['messages']
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return 'end'
    # Otherwise if there is, we continue
    else:
        return 'continue'


graph_builder.add_node('agent', chatbot)
graph_builder.add_node('tools', tool_node)

graph_builder.add_edge(START, 'agent')
graph_builder.add_conditional_edges('agent', should_continue, {'continue': 'tools', 'end': END})
graph_builder.add_edge('tools', 'agent')

# graph = graph_builder.compile(checkpointer=memory)
graph = graph_builder.compile()
print(graph)

async def main():
    

    user_name = 'jess'
    print(user_name)

    await client.add_episode(
        name='User Creation',
        episode_body=(f'{user_name} is interested in buying a Dell Pro Max 14 Premium laptop'),
        source=EpisodeType.text,
        reference_time=datetime.now(timezone.utc),
        source_description='Dell Support Agent',
    )

    # let's get Jess's node uuid
    nl = await client._search(user_name, NODE_HYBRID_SEARCH_EPISODE_MENTIONS)

    user_node_uuid = nl.nodes[0].uuid

    # # and the ManyBirds node uuid
    # nl = await client._search('ManyBirds', NODE_HYBRID_SEARCH_EPISODE_MENTIONS)
    # manybirds_node_uuid = nl.nodes[0].uuid
    print(user_node_uuid)

    ai_result = await graph.ainvoke(
        {
            'messages': [
                {
                    'role': 'user',
                    'content': 'Dell Pro Max 14 battery specifications?',
                }
            ],
            'user_name': user_name,
            'user_node_uuid': user_node_uuid,
        },
        config={'configurable': {'thread_id': uuid.uuid4().hex}},
    )

    print(ai_result)
    msgs = ai_result['messages']

        # 1) The user question is your first HumanMessage

    question = next(m for m in msgs if isinstance(m, HumanMessage)).content

    # 2) The raw tool output is the first ToolMessage

    search_results = next((m.content for m in msgs if isinstance(m, ToolMessage)), None)

    # 3) The final AIMessage (after tool) is the last AIMessage

    response = list(m for m in msgs if isinstance(m, AIMessage))[-1].content

    print(f"\nQuestion:\n{question}\n")

    print(f"Answer:\n{response}\n")

    if search_results:

        print(f"Search Results:\n{search_results}\n")

    # 1) Close the Graphiti / Neo4j driver
    await client.driver.close()

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())