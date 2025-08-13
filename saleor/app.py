import requests
import json
import os

SALEOR_ENDPOINT = os.getenv("SALEOR_ENDPOINT", "https://store-gqt4azfa.saleor.cloud/graphql/")
SALEOR_TOKEN = os.getenv("SALEOR_TOKEN", "REPLACE_WITH_YOUR_API_TOKEN")
CHANNEL_SLUG = os.getenv("CHANNEL_SLUG", "default-channel")

query = """
query Ping($channel: String!) {
  products(first: 10, channel: $channel) {
    edges {
      node {
        id
        name
        category {
          id
          name
        }
      }
    }
  }
}
"""

variables = {"channel": CHANNEL_SLUG}

response = requests.post(
    SALEOR_ENDPOINT,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SALEOR_TOKEN}",
    },
    json={"query": query, "variables": variables},
)

print("Status code:", response.status_code)
print(json.dumps(response.json(), indent=2))
