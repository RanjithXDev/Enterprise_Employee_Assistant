import os

from agents.orchestration_agent import create_orchestration_agent


def main():

    access_token = os.getenv("COGNITO_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError(
            "COGNITO_ACCESS_TOKEN environment variable is required"
        )

    orchestration_agent = create_orchestration_agent(access_token)

    print("Orchestration Agent created successfully.")
    print()

    print("Test request:")
    print("Requester ID: EMP001")
    print("Request: Show me the details of ticket INC-1001")
    print()

    response = orchestration_agent(
    "Requester ID: EMP001\n"
    "Request: How many leaves do I have remaining?"
    )

    print("Orchestration Agent response:")
    print(response)


if __name__ == "__main__":
    main()