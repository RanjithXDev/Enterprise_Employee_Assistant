from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

GATEWAY_URL = (
    "https://enterpriseassistant-enterpriseassistantgateway-e7knwkygor"
    ".gateway.bedrock-agentcore.ap-south-1.amazonaws.com/mcp"
)


def create_gateway_mcp_client(access_token: str) -> MCPClient:
    if not access_token:
        raise ValueError("Access token is required")

    def transport():
        return streamablehttp_client(
            GATEWAY_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json, text/event-stream",
            },
        )

    return MCPClient(
        transport_callable=transport,
        application_name="EnterpriseAssistant",
        application_version="1.0.0",
    )