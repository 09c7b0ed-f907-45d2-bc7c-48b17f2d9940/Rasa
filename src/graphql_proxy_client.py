from typing import Any, Dict, Optional, TypedDict

import requests


class GraphQLPayload(TypedDict):
    query: str
    variables: Dict[str, Any]


class ProxyRequestPayload(TypedDict):
    operation: str
    target: str
    url: str
    payload: GraphQLPayload


class GraphQLProxyClient:
    def __init__(self, proxy_url: str, graphql_url: str):
        self.proxy_url = proxy_url
        self.graphql_url = graphql_url

    def query(self, query_str: str, session_token: str, variables: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        headers = {"Content-Type": "application/json", "Cookie": f"next-auth.session-token={session_token}"}

        proxy_payload: ProxyRequestPayload = {
            "operation": "query",
            "target": "graphql",
            "url": self.graphql_url,
            "payload": {"query": query_str, "variables": variables or {}},
        }

        try:
            response = requests.post(self.proxy_url, headers=headers, json=proxy_payload)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"[GraphQLProxyClient] Error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            print(f"[GraphQLProxyClient] Request failed: {e}")
            return None
