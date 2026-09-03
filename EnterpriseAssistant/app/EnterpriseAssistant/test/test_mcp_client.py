import os

from mcp_client.gateway_client import create_gateway_mcp_client


def main():
    access_token = os.getenv("COGNITO_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError(
            "COGNITO_ACCESS_TOKEN environment variable is required"
        )

    client = create_gateway_mcp_client(access_token)

    try:
        print("Connecting to AgentCore Gateway...")

        client.__enter__()

        print("MCP session initialized successfully.")

        tools = client.list_tools_sync()

        print(f"Discovered {len(tools)} tool(s):")

        for tool in tools:
            print(f"- {tool}")

    except Exception as exc:
        print("MCP connection failed:")
        print(type(exc).__name__, exc)
        raise

    finally:
        client.__exit__(None, None, None)


if __name__ == "__main__":
    main()