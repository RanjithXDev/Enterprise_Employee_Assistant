from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient


GATEWAY_URL = (
    "https://enterpriseassistant-enterpriseassistantgateway-6ie6qgg3rr"
    ".gateway.bedrock-agentcore.ap-south-1.amazonaws.com/mcp"
)


def create_gateway_mcp_client(access_token: str) -> MCPClient:
    return MCPClient(
        lambda: streamablehttp_client(
            GATEWAY_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )
    )