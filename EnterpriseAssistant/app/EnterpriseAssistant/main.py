from typing import Any
import uuid

from bedrock_agentcore.runtime import (
    BedrockAgentCoreApp,
    BedrockAgentCoreContext,
)

from agents.orchestration_agent import create_orchestration_agent
from services.auth_service import get_authenticated_user
from services.conversation_service import (
    create_conversation,
    get_conversation,
    touch_conversation,
)


app = BedrockAgentCoreApp()
log = app.logger


def _get_usage_value(usage: Any, key: str) -> int:
    """Read a token usage value from either a dict or an object."""
    if isinstance(usage, dict):
        return int(usage.get(key, 0) or 0)

    return int(getattr(usage, key, 0) or 0)


def strip_trailing_tool_use(messages: Any) -> list[dict]:
    """Strip toolUse blocks from the tail until the last message has none."""
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")

    messages = list(messages)

    while messages:
        last = messages[-1]

        if not isinstance(last, dict):
            raise ValueError("each message must be an object")

        original_content = last.get("content", [])

        if (
            not isinstance(original_content, list)
            or not all(isinstance(block, dict) for block in original_content)
        ):
            raise ValueError(
                "each message content value must be a list of content blocks"
            )

        content = [
            block
            for block in original_content
            if "toolUse" not in block
        ]

        if len(content) == len(original_content):
            break

        if content:
            messages[-1] = {
                **last,
                "content": content,
            }
            break

        messages.pop()

    return messages


def _extract_prompt(payload: dict):
    """
    Accept validated harness messages, tool results,
    or a plain prompt string.
    """

    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    if "messages" in payload:
        return strip_trailing_tool_use(payload["messages"])

    if "tool_results" in payload:
        tool_results = payload["tool_results"]

        if not isinstance(tool_results, list) or not all(
            isinstance(tool_result, dict)
            and isinstance(tool_result.get("toolUseId"), str)
            for tool_result in tool_results
        ):
            raise ValueError(
                "tool_results must contain objects with a toolUseId string"
            )

        return [
            {
                "role": "user",
                "content": [
                    {
                        "toolResult": {
                            "toolUseId": tr["toolUseId"],
                            "status": tr.get("status", "success"),
                            "content": tr.get("content", []),
                        }
                    }
                    for tr in tool_results
                ],
            }
        ]

    prompt = payload.get("prompt", "")

    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")

    return prompt


def _has_inline_function_call(messages) -> bool:
    """
    Return True if messages contains an assistant toolUse
    for an inline function tool.
    """

    return False


def _is_inline_function_call(event: dict) -> bool:
    """
    Check if a contentBlockStart event is for an inline function tool.
    """

    return False


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Enterprise Employee Assistant")

    # ---------------------------------------------------------
    # 1. Get authenticated Cognito access token
    # ---------------------------------------------------------

    headers = BedrockAgentCoreContext.get_request_headers() or {}

    authorization = headers.get("Authorization")

    if not authorization:
        raise ValueError("Authorization header is required")

    if not authorization.startswith("Bearer "):
        raise ValueError(
            "Authorization header must contain a Bearer token"
        )

    access_token = authorization.removeprefix("Bearer ").strip()

    if not access_token:
        raise ValueError("Bearer access token is empty")

    # ---------------------------------------------------------
    # 2. Get AgentCore Runtime session ID
    # ---------------------------------------------------------

    request_session_id = None

    if isinstance(payload, dict):
        request_session_id = payload.get("session_id")

    if request_session_id is not None and not isinstance(
        request_session_id,
        str,
    ):
        raise ValueError("session_id must be a string")

    session_id = (
        request_session_id
        or BedrockAgentCoreContext.get_session_id()
        or getattr(context, "session_id", None)
    )

    if not session_id:
        session_id = uuid.uuid4().hex

    # ---------------------------------------------------------
    # 3. Resolve authenticated Cognito user
    # ---------------------------------------------------------

    authenticated_user = get_authenticated_user(access_token)

    if (
        not authenticated_user.employee_id
        and not authenticated_user.is_admin
    ):
        raise ValueError(
            "Authenticated user is not associated with an employee ID"
        )

    actor_id = (
        authenticated_user.employee_id
        or authenticated_user.username
    )

    user_role = (
        "ITAdmin"
        if authenticated_user.is_admin
        else "Employee"
    )

    # ---------------------------------------------------------
    # 4. Extract the user request
    # ---------------------------------------------------------

    prompt = _extract_prompt(payload)

    # ---------------------------------------------------------
    # 5. Create / get conversation metadata
    # ---------------------------------------------------------

    conversation = get_conversation(
        actor_id=actor_id,
        session_id=session_id,
    )

    if conversation is None:

        # Use the first user prompt as the conversation title.
        if isinstance(prompt, str):
            title = prompt.strip()
        else:
            title = "New Conversation"

        if not title:
            title = "New Conversation"

        # Keep the sidebar title short.
        title = title[:80]

        conversation = create_conversation(
            actor_id=actor_id,
            session_id=session_id,
            title=title,
        )

    log.info(
        "Authenticated Requester: %s, role: %s, groups: %s",
        actor_id,
        user_role,
        authenticated_user.groups,
    )

    # ---------------------------------------------------------
    # 6. Initialize observability
    # ---------------------------------------------------------

    observability = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "tools": [],
    }

    # ---------------------------------------------------------
    # 7. Create the Orchestration Agent
    # ---------------------------------------------------------

    agent = create_orchestration_agent(
        actor_id=actor_id,
        session_id=session_id,
        access_token=access_token,
        user_role=user_role,
        employee_id=authenticated_user.employee_id,
        observability=observability,
    )

    # ---------------------------------------------------------
    # 8. Stream the Orchestration Agent response
    #    and collect observability metrics
    # ---------------------------------------------------------

    async for event in agent.stream_async(prompt):

        if not isinstance(event, dict):
            continue

        # ---------------------------------------------
        # Final AgentResult
        # ---------------------------------------------

        result = event.get("result")

        if result is not None:
            metrics = getattr(result, "metrics", None)

            if metrics is not None:

                # -----------------------------------------
                # Token usage
                # -----------------------------------------

                usage = getattr(
                    metrics,
                    "accumulated_usage",
                    None,
                )

                if usage is not None:
                    input_tokens = _get_usage_value(
                        usage,
                        "inputTokens",
                    )

                    output_tokens = _get_usage_value(
                        usage,
                        "outputTokens",
                    )

                    total_tokens = _get_usage_value(
                        usage,
                        "totalTokens",
                    )

                    observability["input_tokens"] += input_tokens
                    observability["output_tokens"] += output_tokens
                    observability["total_tokens"] += total_tokens

                    log.info(
                        "Token usage: input=%s output=%s total=%s",
                        input_tokens,
                        output_tokens,
                        total_tokens,
                    )

                # -----------------------------------------
                # Tool metrics
                # -----------------------------------------

                tool_metrics = getattr(
                    metrics,
                    "tool_metrics",
                    {},
                ) or {}

                for tool_name, tool_metric in tool_metrics.items():

                    tool_record = {
                        "name": tool_name,
                        "calls": getattr(
                            tool_metric,
                            "call_count",
                            0,
                        ),
                        "success": getattr(
                            tool_metric,
                            "success_count",
                            0,
                        ),
                        "errors": getattr(
                            tool_metric,
                            "error_count",
                            0,
                        ),
                        "duration": getattr(
                            tool_metric,
                            "total_time",
                            0,
                        ),
                    }

                    observability["tools"].append(
                        tool_record
                    )

                    log.info(
                        "Tool metrics: name=%s calls=%s "
                        "success=%s errors=%s duration=%s",
                        tool_name,
                        tool_record["calls"],
                        tool_record["success"],
                        tool_record["errors"],
                        tool_record["duration"],
                    )

            # IMPORTANT:
            # Do not yield the raw AgentResult.
            continue

        # ---------------------------------------------
        # Preserve normal streaming events
        # ---------------------------------------------

        if "event" not in event:
            continue

        cbs = event["event"].get("contentBlockStart")

        if cbs is not None and not cbs.get("start"):
            continue

        yield event

    # ---------------------------------------------------------
    # 9. Update conversation timestamp
    # ---------------------------------------------------------

    touch_conversation(
        actor_id=actor_id,
        session_id=session_id,
    )

    # ---------------------------------------------------------
    # 10. Log and emit observability
    # ---------------------------------------------------------

    log.info(
        "Final observability: %s",
        observability,
    )

    yield {
        "conversation": {
            "session_id": session_id,
        },
        "observability": observability,
    }


if __name__ == "__main__":
    app.run()