from strands import Agent, tool

from model.load import load_model
from agents.hr_agent import create_hr_agent
from agents.it_agent import create_it_agent
from memory.session import get_memory_session_manager


def create_orchestration_agent(
    actor_id: str,
    session_id: str,
    access_token: str,
    user_role: str
):
    model = load_model()

    # Create HR Agent once for this orchestration request.
    hr_agent = create_hr_agent()

    @tool
    def ask_it_agent(request: str) -> str:
        """
        Delegate an IT request to the IT Support Agent.
        The authenticated requester identity is supplied by the
        orchestration layer and is never taken from the user's request.
        """

        if not request:
            return "Request is required."

        # actor_id is trusted application identity.
        delegated_request = (
            f"Requester ID: {actor_id}\n"
            f"User Role: {user_role}\n"
            f"Request: {request}"
        )

        it_agent, gateway_mcp_client = create_it_agent(access_token)

        try:
            response = it_agent(delegated_request)
            return str(response)

        finally:
            gateway_mcp_client.__exit__(None, None, None)

    @tool
    def ask_hr_agent(request: str) -> str:
        """
        Delegate an HR request to the HR Support Agent.
        The authenticated requester identity is supplied by the
        orchestration layer.
        """

        if not request:
            return "Request is required."

        delegated_request = (
            f"Requester ID: {actor_id}\n"
            f"Request: {request}"
        )

        response = hr_agent(delegated_request)

        return str(response)

    # Use the centralized AgentCore Memory configuration.
    session_manager = get_memory_session_manager(
        session_id=session_id,
        actor_id=actor_id,
    )

    orchestration_agent = Agent(
        model=model,
        system_prompt="""
You are the Orchestration Agent for an Enterprise Employee Assistant.

ROLE:

You understand employee requests, identify the appropriate domain,
and delegate requests to specialized agents.

You are NOT responsible for directly solving IT or HR problems.

AVAILABLE SPECIALIZED AGENTS:

1. IT Agent

Handles:
- Laptop and device issues
- Network and Wi-Fi problems
- VPN issues
- Password and account issues
- IT support requests
- IT incidents
- IT ticket creation
- IT ticket retrieval
- IT ticket updates
- IT ticket closing
- IT policies and troubleshooting

2. HR Agent

Handles:
- Leave-related questions
- Company holidays
- HR policies
- Employee information
- Benefits-related questions
- Other HR-related requests

REQUEST ROUTING:

- Route IT-related requests to ask_it_agent.
- Route HR-related requests to ask_hr_agent.
- If a request belongs to neither domain, explain that it is
  outside the currently supported domains.
- If a request is genuinely ambiguous, ask the employee for clarification.

IDENTITY:

The application provides the authenticated Requester ID.

The Requester ID is trusted application context.

Rules:

1. NEVER ask the employee to provide a Requester ID.
2. NEVER modify, replace, infer, or invent the Requester ID.
3. NEVER use an employee ID contained inside a ticket as the Requester ID.
4. The delegation tools automatically use the authenticated Requester ID.
5. Never bypass backend authorization.
6. Never override an authorization failure.
7. Never claim authorization unless the backend confirms it.

DELEGATION:

When delegating:

- Pass the complete original employee request.
- Do not replace the request with a vague summary.
- Do not delegate an empty request.

IT REQUESTS:

Delegate IT-related requests to ask_it_agent.

HR REQUESTS:

Delegate HR-related requests to ask_hr_agent.

IMPORTANT:

- Do not directly answer IT questions when the IT Agent should handle them.
- Do not directly answer HR questions when the HR Agent should handle them.
- Do not fabricate ticket IDs.
- Do not fabricate employee information.
- Do not fabricate leave information.
- Do not fabricate company policies.
- Do not claim an action was completed unless the specialized agent
  or backend tool confirms successful execution.
- Do not claim authorization unless the backend confirms it.
- If a tool returns an error or access-denied response, report it accurately.
- Do not expose internal tool names or implementation details to employees.

RESPONSE:

For successful delegation, provide the specialized agent's result
clearly and concisely.

For authorization failures, report the authorization failure accurately.

For missing or unclear information, ask only for information necessary
to continue.
""",
        tools=[
            ask_it_agent,
            ask_hr_agent,
        ],
        session_manager=session_manager,
    )

    return orchestration_agent