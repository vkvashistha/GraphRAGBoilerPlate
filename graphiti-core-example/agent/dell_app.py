import asyncio
import json
import logging
import os
import sys
import uuid
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

# import ipywidgets as widgets
from dotenv import load_dotenv
# from IPython.display import Image, display
from typing_extensions import TypedDict

load_dotenv()

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()

# Configure Graphiti
from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodeType
from graphiti_core.utils.maintenance.graph_data_operations import clear_data

neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

client = Graphiti(
    neo4j_uri,
    neo4j_user,
    neo4j_password,
)

# Import Dell episodes data
from data import episodes

async def ingest_dell_episodes(client: Graphiti):
    # Clear existing data (optional - uncomment if needed)
    # await clear_data(client)
    
    # Build indices and constraints
    await client.build_indices_and_constraints()
    
    logger.info("Adding Dell episodes to Graphiti...")
    # Ingest all Dell episodes from data.py
    for i, episode in enumerate(episodes):
        # Convert content to string if it's not already a string
        episode_body = episode['content'] if isinstance(episode['content'], str) else json.dumps(episode['content'])
            
        await client.add_episode(
            name=f"Dell Pro Max 14 - Episode {i+1}: {episode['description']}",
            episode_body=episode_body,
            source_description=f"Dell Pro Max 14 Premium - {episode['description']}",
            source=episode['type'],
            reference_time=datetime.now(timezone.utc),
        )
        logger.info(f"Added episode: Dell Pro Max 14 - Episode {i+1} ({episode['description']})")


from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_EPISODE_MENTIONS

async def main():
    try:
        # Ingest Dell episodes
        await ingest_dell_episodes(client)
        
        # Create user node
        user_name = 'alex'
        
        await client.add_episode(
            name='User Creation',
            episode_body=(f'{user_name} owns a Dell Pro Max 14 Premium MA14250 and needs technical support'),
            source=EpisodeType.text,
            reference_time=datetime.now(timezone.utc),
            source_description='Dell Support Agent',
        )
        logger.info(f"Created user node for {user_name}")
        
        # Get the user's node UUID
        logger.info(f"Retrieving node UUID for user: {user_name}")
        nl = await client._search(user_name, NODE_HYBRID_SEARCH_EPISODE_MENTIONS)
        
        if not nl.nodes:
            logger.error(f"No node found for user: {user_name}")
            user_node_uuid = None
        else:
            user_node_uuid = nl.nodes[0].uuid
            logger.info(f"Found user node UUID: {user_node_uuid}")
        
        # Get the Dell device node UUID
        logger.info("Retrieving node UUID for Dell Pro Max 14 Premium")
        nl = await client._search('Dell Pro Max 14 Premium', NODE_HYBRID_SEARCH_EPISODE_MENTIONS)
        
        if not nl.nodes:
            logger.error("No node found for Dell Pro Max 14 Premium")
            dell_device_node_uuid = None
        else:
            dell_device_node_uuid = nl.nodes[0].uuid
            logger.info(f"Found Dell device node UUID: {dell_device_node_uuid}")
            
        # Return the UUIDs for potential further use
        return user_node_uuid, dell_device_node_uuid
        
    finally:
        # Close the client connection
        await client.close()
        logger.info("Graphiti client connection closed")


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())