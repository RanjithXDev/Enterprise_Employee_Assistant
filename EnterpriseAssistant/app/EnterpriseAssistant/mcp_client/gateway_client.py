from strands.tools.mcp import MCPClient

GATEWAY_URL = (
    "https://enterpriseassistant-enterpriseassistantgateway-e7knwkygor"
    ".gateway.bedrock-agentcore.ap-south-1.amazonaws.com/mcp"
)


def create_gateway_mcp_client(access_token: str) -> MCPClient:
    if not access_token:
        raise ValueError("Access token is required")

    return MCPClient(
        url=GATEWAY_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        application_name="EnterpriseAssistant",
        application_version="1.0.0",
    )