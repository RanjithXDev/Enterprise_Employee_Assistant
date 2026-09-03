import os

from agents.it_agent import create_it_agent


def main():
    access_token = os.getenv("COGNITO_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError(
            "COGNITO_ACCESS_TOKEN environment variable is required"
        )

    agent, gateway_mcp_client = create_it_agent(access_token)

    try:
        print("IT Agent created successfully.")
        print()
        print("Sending request...")
        print("Requester ID: EMP001")
        print("Request: Show me the details of ticket INC-1001")
        print()

        response = agent(
            "Requester ID: EMP001\n"
            "Request: Show me the details of ticket INC-1001"
        )

        print("IT Agent response:")
        print(response)

    finally:
        gateway_mcp_client.__exit__(None, None, None)


if __name__ == "__main__":
    main()
