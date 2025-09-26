from __future__ import annotations

from typing import Dict, Iterable

from src.executor.graphql_translator import GraphQLRequestSpec
from src.graphql.graphql_proxy_client import GraphQLProxyClient
from src.graphql.graphql_response import MetricsQueryResponse


class GraphQLRunner:
    """Thin wrapper around GraphQLProxyClient to run many requests."""

    def __init__(self, client: GraphQLProxyClient):
        self.client = client

    def run_many(self, requests: Iterable[GraphQLRequestSpec], session_token: str) -> Dict[str, MetricsQueryResponse]:
        results: Dict[str, MetricsQueryResponse] = {}
        for spec in requests:
            resp = self.client.query(spec["query"], session_token, variables=spec.get("variables", {}))
            if resp is not None:
                results[spec["kpi_id"]] = resp
        return results
