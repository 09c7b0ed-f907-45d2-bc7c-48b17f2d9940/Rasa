from typing import Any

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


class GraphQLClient:
    def __init__(self, url: str) -> None:
        self.url: str = url

    def query(self, query_str: str, token: str) -> dict[str, Any]:
        transport = RequestsHTTPTransport(
            url=self.url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql(query_str)
        return client.execute(query)  # type: ignore
