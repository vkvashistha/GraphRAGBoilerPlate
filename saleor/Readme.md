# Saleor GraphQL Tool Agent (LangGraph)

A minimal, working LangGraph agent that uses a single GraphQL tool to query a Saleor API and summarizes results. It runs an interactive REPL.

## Requirements
- Python 3.10+
- OpenAI API key
- Optional: Saleor API token (if your endpoint requires auth)

## Install
From the `saleor/` directory:
```bash
pip install -r requirements.txt
```

## Configure environment
Create a `.env` file next to this script with:
```env
OPENAI_API_KEY=sk-...
SALEOR_ENDPOINT=https://store-gqt4azfa.saleor.cloud/graphql/
SALEOR_TOKEN=REPLACE_WITH_YOUR_API_TOKEN
CHANNEL_SLUG=default-channel
OPENAI_MODEL=gpt-4o-mini
```
Notes:
- If your endpoint is public, you can keep `SALEOR_TOKEN` as the placeholder and it won’t send an auth header.
- For any availability/publication/pricing queries, the agent will include `channel: "<CHANNEL_SLUG>"` automatically.

## Run
```bash
python saleor_langgraph_graphqltool_agent.py
```
You should see:
```
Saleor GraphQL Tool Agent ready. Type 'exit' to quit.
```

## Run with LangGraph Studio (langgraph dev)
 
1. Install the CLI (once):
```bash
pip install -U langgraph-cli
```
2. Start Studio from this directory:
```bash
langgraph dev --open
```
- It will load `langgraph.json` and `.env` automatically.
- Graph ID: `tools_and_llm_2` -> `saleor_langgraph_graphqltool_agent.py:app`.
- Select the graph in the UI and start chatting.

## Use (examples)
Type natural language requests; the agent composes and executes Saleor GraphQL.
- "List first 5 products with name and pricing in the default channel"
- "Get details for product 'Coffee Mug' including publication status"

## How it works
- File: `saleor/saleor_langgraph_graphqltool_agent.py`
- LLM: `langchain_openai.ChatOpenAI` bound to one tool
- Tool: `langchain_community.tools.graphql.tool.BaseGraphQLTool` with `GraphQLAPIWrapper`
- Schema is fetched from the endpoint; the tool description enforces using `channel` for availability/publication/pricing.

## Troubleshooting
- Auth errors: set a valid `SALEOR_TOKEN`.
- Network/schema errors: verify `SALEOR_ENDPOINT` is reachable.
- OpenAI errors: confirm `OPENAI_API_KEY` and `OPENAI_MODEL`.
