# file: saleor_langgraph_graphqltool_agent.py
import os
from typing import Any, List
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode

# Use GraphQL wrapper + tool from langchain_community
from langchain_community.utilities.graphql import GraphQLAPIWrapper
from langchain_community.tools.graphql.tool import BaseGraphQLTool

# ---------------------------------
# Config
# ---------------------------------
SALEOR_ENDPOINT = os.getenv("SALEOR_ENDPOINT", "https://store-gqt4azfa.saleor.cloud/graphql/")
SALEOR_TOKEN    = os.getenv("SALEOR_TOKEN", "REPLACE_WITH_YOUR_API_TOKEN")
CHANNEL_SLUG    = os.getenv("CHANNEL_SLUG", "default-channel")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ---------------------------------
# GraphQL tool using the wrapper (with optional auth headers)
# ---------------------------------
headers = {"Authorization": f"Bearer {SALEOR_TOKEN}"} if SALEOR_TOKEN and SALEOR_TOKEN != "REPLACE_WITH_YOUR_API_TOKEN" else None
graphql_wrapper = GraphQLAPIWrapper(
    graphql_endpoint=SALEOR_ENDPOINT,
    custom_headers=headers,
    fetch_schema_from_transport=True,
)

# Tailor the description for Saleor to avoid invalid fields like `allProducts`
graphql_tool = BaseGraphQLTool(
    graphql_wrapper=graphql_wrapper,
    # description=(
    #     "Input is a valid Saleor GraphQL query/mutation string. Use Query.products or product; "
    #     f'include channel: "{CHANNEL_SLUG}" where required; prefer isAvailable on Product without channel '
    #     "if your schema doesn't accept the channel argument."
    # ),
    # replace your current description with:
    description=(
    "Input is a valid Saleor GraphQL query/mutation string. "
    "For ANY availability/publication/pricing, ALWAYS pass the channel argument "
    f'and call product(..., channel: "{CHANNEL_SLUG}"). '
    "Never use isAvailable without a channel. Prefer Product.channelListings "
    "for the target channel (isPublished, availableForPurchaseAt, visibleInListings)."
)

)

TOOLS = [graphql_tool]


SYSTEM_PROMPT = f"""You are a Saleor shopping copilot that uses exactly ONE tool: query_graphql.
Generate the required GraphQL (query or mutation) and call the tool. Then summarize results clearly.

"""
llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0).bind_tools(TOOLS)

# ---------------------------------
# Minimal graph
# ---------------------------------

def _sanitize_for_llm(messages: List[Any]) -> List[Any]:
    clean: List[Any] = []
    pending_tools_allowed = False
    for m in messages:
        if isinstance(m, AIMessage):
            clean.append(m)
            pending_tools_allowed = bool(getattr(m, "tool_calls", None))
        elif isinstance(m, ToolMessage):
            if pending_tools_allowed:
                clean.append(m)
        else:
            clean.append(m)
            pending_tools_allowed = False
    return clean


def call_llm(state: MessagesState):
    history = _sanitize_for_llm(state["messages"])  # avoid orphan ToolMessages
    msgs = [SystemMessage(content=SYSTEM_PROMPT)] + history
    ai = llm.invoke(msgs)
    return {"messages": [ai]}


tool_node = ToolNode(TOOLS)


def should_continue(state: MessagesState):
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


graph = StateGraph(MessagesState)
graph.add_node("llm", call_llm)
graph.add_node("tool_exec", tool_node)
graph.add_conditional_edges("llm", should_continue, {"tools": "tool_exec", END: END})
graph.add_edge("tool_exec", "llm")
graph.set_entry_point("llm")
app = graph.compile()

# ---------------------------------
# Simple REPL driver
# ---------------------------------
if __name__ == "__main__":
    state: MessagesState = {"messages": []}
    print("Saleor GraphQL Tool Agent ready. Type 'exit' to quit.")
    while True:
        user = input("\nYou: ")
        if user.strip().lower() == "exit":
            break
        state["messages"].append(HumanMessage(content=user))
        state = app.invoke(state)
        ai = next(m for m in reversed(state["messages"]) if isinstance(m, AIMessage))
        print("\nAssistant:", ai.content)
