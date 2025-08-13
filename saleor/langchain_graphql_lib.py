from langchain_community.tools.graphql.tool import BaseGraphQLTool
from langchain_community.utilities.graphql import GraphQLAPIWrapper
from langchain.agents import initialize_agent, AgentType
from langchain_openai import OpenAI

import os
import json
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
SALEOR_ENDPOINT = os.getenv("SALEOR_ENDPOINT", "https://store-gqt4azfa.saleor.cloud/graphql/")
SALEOR_TOKEN = os.getenv("SALEOR_TOKEN", "REPLACE_WITH_YOUR_API_TOKEN")
CHANNEL_SLUG = os.getenv("CHANNEL_SLUG", "default-channel")
api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
model = os.getenv("OPENAI_MODEL", "gpt-4-vision-preview")

headers={
        # "Content-Type": "application/json",
        "Authorization": f"Bearer {SALEOR_TOKEN}",
    }

# 1. Initialize the GraphQL wrapper with your endpoint
# graphql_wrapper = GraphQLAPIWrapper(graphql_endpoint="https://api.my-ecommerce.com/graphql")
graphql_wrapper = GraphQLAPIWrapper(graphql_endpoint=SALEOR_ENDPOINT, custom_headers=headers)

# 2. Create the GraphQL tool using the wrapper
# The description is what the LLM will see and use to understand the tool's purpose.
graphql_tool = BaseGraphQLTool(graphql_wrapper=graphql_wrapper)

# 3. Initialize an agent with the tool
llm = OpenAI(temperature=0, api_key=api_key, model=model)
tools = [graphql_tool]

agent = initialize_agent(
    tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
)

# 4. Run the agent with a natural language query
# agent.run("What are the names and prices of all running shoes available?")
agent.run("Carrot Juice are available or not?")