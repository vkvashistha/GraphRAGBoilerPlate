# file: saleor_introspection_agent.py
"""
A minimal, self-contained example that follows an agentic pattern with:
- Introspection tool: fetches GraphQL schema from Saleor
- Simple agent logic: inspects schema to decide how to query products for a user's request
- Executor tool: executes the constructed GraphQL query against Saleor

This does NOT modify your LangGraph agent. It's a separate script to illustrate the
introspection-driven approach tailored to Saleor.
"""

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

# --- Step 1: Introspection Tool ---
INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          name
          description
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
        }
      }
      inputFields {
        name
        description
      }
    }
    queryType { name }
    mutationType { name }
  }
}
"""

def _headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SALEOR_TOKEN}",
    }

def get_graphql_schema_tool() -> Dict[str, Any]:
    """Introspect the endpoint and return the __schema JSON object."""
    with httpx.Client(timeout=45.0) as client:
        resp = client.post(SALEOR_ENDPOINT, headers=_headers(), json={"query": INTROSPECTION_QUERY})
        resp.raise_for_status()
        j = resp.json()
        if "errors" in j:
            raise RuntimeError(f"Introspection failed with GraphQL errors: {j['errors']}")
        data = j.get("data", {})
        schema = data.get("__schema")
        if not schema:
            raise RuntimeError("No __schema in introspection response")
        return schema

# --- Step 2: Agent Logic (very simple heuristic) ---

def _find_type(schema: Dict[str, Any], type_name: str) -> Optional[Dict[str, Any]]:
    for t in schema.get("types", []):
        if t.get("name") == type_name:
            return t
    return None

def _find_field(type_obj: Dict[str, Any], field_name: str) -> Optional[Dict[str, Any]]:
    for f in (type_obj.get("fields") or []):
        if f.get("name") == field_name:
            return f
    return None

def _has_arg(field_obj: Dict[str, Any], arg_name: str) -> bool:
    for a in (field_obj.get("args") or []):
        if a.get("name") == arg_name:
            return True
    return False

def agent_logic(user_request: str, graphql_schema: Dict[str, Any]) -> str:
    """Very small demo of using schema to decide how to query products.

    - If the user asks to find/search products, we look for the `products` field in the Query type.
    - We detect if it supports a `search` arg or a `where` arg and construct the appropriate query.
    - We always include `channel` per Saleor requirements for price-aware results.

    Returns: a GraphQL query string, or a short message if we cannot handle the request.
    """
    req = user_request.strip().lower()
    wants_search = ("search for" in req) or ("find" in req) or ("show" in req)

    try:
        query_type_name = graphql_schema.get("queryType", {}).get("name")
        if not query_type_name:
            return "Couldn't find the root Query type in schema."
        query_type = _find_type(graphql_schema, query_type_name)
        if not query_type:
            return f"Type '{query_type_name}' not found in schema."

        # Prefer products listing for search-like requests
        if wants_search:
            products_field = _find_field(query_type, "products")
            if not products_field:
                return "The API doesn't expose a 'products' field on Query."

            # Heuristics: prefer 'search' if present, else try 'where'
            supports_search = _has_arg(products_field, "search")
            supports_where = _has_arg(products_field, "where")

            # Use the user input as the search term (crude extraction for demo)
            # e.g., "find me running shoes" -> search_term = "running shoes"
            search_term = user_request

            if supports_search:
                return f"""
query {{
  products(first: 10, channel: "{CHANNEL_SLUG}", search: "{search_term}") {{
    edges {{
      node {{
        id
        name
        slug
        category {{ name }}
        variants {{ id name sku }}
      }}
    }}
    pageInfo {{ hasNextPage endCursor }}
  }}
}}"""
            elif supports_where:
                # Fallback to a where filter that attempts full-text search if available in your schema.
                # ProductWhereInput in Saleor often contains a 'search' field.
                return f"""
query {{
  products(first: 10, channel: "{CHANNEL_SLUG}", where: {{ search: "{search_term}" }}) {{
    edges {{
      node {{
        id
        name
        slug
        category {{ name }}
        variants {{ id name sku }}
      }}
    }}
    pageInfo {{ hasNextPage endCursor }}
  }}
}}"""
            else:
                # As a last resort, just query without search filters
                return f"""
query {{
  products(first: 10, channel: "{CHANNEL_SLUG}") {{
    edges {{ node {{ id name slug category {{ name }} }} }}
    pageInfo {{ hasNextPage endCursor }}
  }}
}}"""

        # Simple example: if request mentions a product by slug
        if "product" in req and "slug:" in req:
            # Extract slug value between quotes if present; else leave placeholder
            slug = "PLACEHOLDER-SLUG"
            return f"""
query {{
  product(slug: "{slug}", channel: "{CHANNEL_SLUG}") {{
    id
    name
    slug
    variants {{ id name sku }}
  }}
}}"""

        return "Sorry, I don't know how to handle that request with this API in this demo."
    except Exception as e:
        return f"Agent error while planning: {e}"

# --- Step 3: Executor Tool ---

def execute_graphql_query_tool(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Executes a given GraphQL query against the Saleor endpoint."""
    with httpx.Client(timeout=45.0) as client:
        resp = client.post(
            SALEOR_ENDPOINT,
            headers=_headers(),
            json={"query": query, "variables": variables or {}},
        )
        resp.raise_for_status()
        j = resp.json()
        return j

# --- Main flow (demo CLI) ---
if __name__ == "__main__":
    try:
        print("Introspecting Saleor schema...")
        schema = get_graphql_schema_tool()
        print("Schema introspected.")

        user_input = input("\nYou: ") or "find me a pair of running shoes"
        print(f"\nUser: {user_input}")

        constructed = agent_logic(user_input, schema)
        if constructed.strip().startswith("query") or constructed.strip().startswith("mutation"):
            print("\nAgent constructed GraphQL:\n")
            print(constructed)

            print("\nExecuting...\n")
            result = execute_graphql_query_tool(constructed)
            print(json.dumps(result, indent=2))
        else:
            print(f"\nAgent: {constructed}")

    except Exception as e:
        print(f"An error occurred: {e}")
