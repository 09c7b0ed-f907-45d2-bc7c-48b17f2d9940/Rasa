from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

class GraphQLClient:
    def __init__(self, url):
        """Initialize the GraphQL client with an endpoint."""
        self.url = url

    def query(self, query_str, token, variables=None):
        """Execute a GraphQL query with a token and optional variables."""
        transport = RequestsHTTPTransport(
            url=self.url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql(query_str)
        return client.execute(query, variable_values=variables)