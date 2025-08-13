# file: saleor_agent.py
import os, json, re, httpx
from typing import Any, Dict, List, Optional, TypedDict
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode

# ---------------------------------
# Config from your example
# ---------------------------------
SALEOR_ENDPOINT = os.getenv("SALEOR_ENDPOINT", "https://store-gqt4azfa.saleor.cloud/graphql/")
SALEOR_TOKEN    = os.getenv("SALEOR_TOKEN", "REPLACE_WITH_YOUR_API_TOKEN")
CHANNEL_SLUG    = os.getenv("CHANNEL_SLUG", "default-channel")

# ---------------------------------
# (Optional) light allow/deny-lists for safety
# Keep it simple: only allow a known set of operations at first.
# Expand as needed for your store.
# ---------------------------------
ALLOWED_OPERATION_NAMES: Optional[set] = None  # set to None to allow all operation names

def _extract_operation_names(query: str) -> List[str]:
    # naive parse to find operation names like: query Foo( or mutation Bar(
    ops = re.findall(r'\b(query|mutation)\s+([A-Za-z_][A-Za-z0-9_]*)', query)
    return [name for _, name in ops]

# ---------------------------------
# Single GraphQL tool
# ---------------------------------
def _gql_post(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {SALEOR_TOKEN}"}
    with httpx.Client(timeout=45.0) as c:
        r = c.post(SALEOR_ENDPOINT, json={"query": query, "variables": variables or {}}, headers=headers)
        r.raise_for_status()
        payload = r.json()
        # Surface GraphQL errors explicitly alongside data
        if isinstance(payload, dict) and payload.get("errors"):
            return payload  # includes both data and errors
        return payload

@tool
def graphql_exec(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a GraphQL operation against Saleor. Input MUST be valid for the Saleor schema.
    The assistant should include the channel for price-aware queries.
    """
    # Optional guardrail: only allow whitelisted operation names
    if ALLOWED_OPERATION_NAMES is not None:
        operation_names = _extract_operation_names(query)
        if operation_names and not all(name in ALLOWED_OPERATION_NAMES for name in operation_names):
            return {
                "error": f"Blocked operation. Allowed: {sorted(ALLOWED_OPERATION_NAMES)}",
                "attempted": operation_names,
            }
    data = _gql_post(query, variables)
    return data

TOOLS = [graphql_exec]

# ---------------------------------
# Prompt: teach the model how to use Saleor with ONE tool.
# ---------------------------------
SCHEMA_HINT = f"""
You are connected to a Saleor GraphQL API. Channel slug to use for price-aware queries is "{CHANNEL_SLUG}".

Product catalog:
- List products (use 'where' filters per Saleor Quickstart):
  Example:
  query {{
    products(first: 10, channel: "{CHANNEL_SLUG}", where: {{ minimalPrice: {{ range: {{ gte: 10, lte: 100 }} }} }}) {{
      edges {{ node {{ id name category {{ id name }} }} }}
      pageInfo {{ hasNextPage endCursor }}
    }}
  }}

- Get product by slug (include variants to find valid variantId):
  query {{
    product(slug: "blue-hoodie", channel: "{CHANNEL_SLUG}") {{
      id name slug variants {{ id name sku }}
    }}
  }}

Checkout (cart) flow:
- Create checkout with variantId(s):
  mutation {{
    checkoutCreate(input: {{ channel: "{CHANNEL_SLUG}", lines: [{{ quantity: 1, variantId: "<VARIANT_ID>" }}] }}) {{
      checkout {{ id token lines {{ id quantity variant {{ id name sku }} }} }}
      errors {{ field message }}
    }}
  }}

- Update addresses and email, then fetch available shipping methods:
  mutation {{
    checkoutShippingAddressUpdate(checkoutId: "<CHECKOUT_ID>", shippingAddress: {{ firstName: "First", lastName: "Last", streetAddress1: "8066 Madison St.", city: "Brooklyn", postalCode: "11237", country: US, countryArea: "NY" }}) {{ errors {{ field message }} }}
    checkoutBillingAddressUpdate(checkoutId: "<CHECKOUT_ID>", billingAddress: {{ firstName: "First", lastName: "Last", streetAddress1: "8066 Madison St.", city: "Brooklyn", postalCode: "11237", country: US, countryArea: "NY" }}) {{ errors {{ field message }} }}
    checkoutEmailUpdate(checkoutId: "<CHECKOUT_ID>", email: "test@test.com") {{ checkout {{ shippingMethods {{ id name }} }} errors {{ field message }} }}
  }}

- Select shipping method:
  mutation {{ checkoutDeliveryMethodUpdate(checkoutId: "<CHECKOUT_ID>", deliveryMethodId: "<METHOD_ID>") {{ errors {{ field message }} }} }}

- Payment and complete (high level):
  mutation {{ checkoutPaymentCreate(checkoutId: "<CHECKOUT_ID>", input: {{ gateway: "<GATEWAY>", amount: 12.34 }}) {{ errors {{ field message }} }} }}
  mutation {{ checkoutComplete(checkoutId: "<CHECKOUT_ID>") {{ order {{ id number }} errors {{ field message }} }} }}

Rules you MUST follow:
- ALWAYS include the channel ("{CHANNEL_SLUG}") for price-aware queries on products/product.
- Prefer minimal selections and include pagination pageInfo when listing.
- Fetch variants before adding to checkout to obtain a valid variantId.
- Reuse checkout id/token across subsequent mutations.
- Ask one clarifying question if required (e.g., size not found).

Output policy:
- When you need store data or to change state, CALL the single tool graphql_exec(query, variables).
- After the tool returns, summarize results clearly (e.g., 5 items, totals, next actions).
"""

SYSTEM_PROMPT = f"""You are a Saleor shopping copilot that uses exactly ONE tool: graphql_exec(query, variables).
Generate the required GraphQL (query or mutation) and call the tool. Then summarize results clearly.

{SCHEMA_HINT}
"""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(TOOLS)

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
            # do not toggle flag; allow multiple tool messages
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
    print("Saleor Agent ready. Type 'exit' to quit.")
    while True:
        user = input("\nYou: ")
        if user.strip().lower() == "exit":
            break
        state["messages"].append(HumanMessage(content=user))
        state = app.invoke(state)
        ai = next(m for m in reversed(state["messages"]) if isinstance(m, AIMessage))
        print("\nAssistant:", ai.content)
