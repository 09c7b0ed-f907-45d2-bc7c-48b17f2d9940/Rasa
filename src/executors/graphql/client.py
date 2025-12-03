import logging
from typing import Any, Dict, Optional, TypedDict

import requests

import src.domain.graphql.response as gqlr


class GraphQLPayload(TypedDict):
    query: str
    variables: Dict[str, Any]


class ProxyRequestPayload(TypedDict):
    operation: str
    target: str
    url: str
    payload: GraphQLPayload


logger = logging.getLogger(__name__)


class GraphQLProxyClient:
    def __init__(self, proxy_url: str, graphql_url: str):
        self.proxy_url = proxy_url
        self.graphql_url = graphql_url

    def query(self, query_str: str, session_token: str, variables: Optional[Dict[str, Any]] = None) -> gqlr.MetricsQueryResponse | None:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {session_token}",
        }

        proxy_payload: ProxyRequestPayload = {
            "operation": "query",
            "target": "graphql",
            "url": self.graphql_url,
            "payload": {"query": query_str, "variables": variables or {}},
        }

        try:
            response = requests.post(self.proxy_url, headers=headers, json=proxy_payload)

            if response.status_code == 200:
                try:
                    return gqlr.MetricsQueryResponse.model_validate(response.json())
                except Exception as e:
                    logger.error("[GraphQLProxyClient] Validation error: %s. Raw: %s", e, response.text)
                    return None
            else:
                content_type = response.headers.get("Content-Type", "")
                preview = response.text[:1000]
                logger.error(
                    "[GraphQLProxyClient] Error %s (Content-Type=%s). Body preview: %s. Query preview: %s",
                    response.status_code,
                    content_type,
                    preview,
                    query_str[:300],
                )
                return None

        except Exception as e:
            logger.error(f"[GraphQLProxyClient] Request failed: {e}")
            return None
