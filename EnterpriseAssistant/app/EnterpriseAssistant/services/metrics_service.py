"""
Emits application metrics as CloudWatch Embedded Metric Format (EMF)
log lines.

EMF metrics require no extra IAM permissions and no extra API calls —
CloudWatch automatically extracts them from specially-structured JSON
log lines that already go to the runtime's existing log group. This is
the mechanism behind the "EnterpriseAssistant-Observability" dashboard.
"""

import json
import time
from typing import Any

_NAMESPACE = "EnterpriseAssistant/Agents"


def _emit_emf(
    dimension_names: list[str],
    dimension_values: dict[str, str],
    metrics: dict[str, tuple[float, str]],
) -> None:
    """
    Print one EMF log line. `metrics` maps metric name -> (value, unit).
    """

    payload: dict[str, Any] = {
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": _NAMESPACE,
                    "Dimensions": [dimension_names],
                    "Metrics": [
                        {"Name": name, "Unit": unit}
                        for name, (_, unit) in metrics.items()
                    ],
                }
            ],
        },
        **dimension_values,
        **{name: value for name, (value, _) in metrics.items()},
    }

    print(json.dumps(payload))


def emit_request_metrics(
    user_role: str,
    success: bool,
    latency_ms: float,
    observability: dict,
) -> None:
    """
    Emit one request-level metric record and one per-tool metric record
    for every tool the request touched.
    """

    role = user_role or "Unknown"

    _emit_emf(
        dimension_names=["UserRole"],
        dimension_values={"UserRole": role},
        metrics={
            "RequestCount": (1, "Count"),
            "RequestErrors": (0 if success else 1, "Count"),
            "RequestLatencyMs": (latency_ms, "Milliseconds"),
            "InputTokens": (observability.get("input_tokens", 0), "Count"),
            "OutputTokens": (observability.get("output_tokens", 0), "Count"),
            "TotalTokens": (observability.get("total_tokens", 0), "Count"),
        },
    )

    for tool in observability.get("tools", []):
        tool_name = tool.get("name", "unknown")

        # `duration` from Strands tool_metrics is in seconds.
        duration_ms = float(tool.get("duration", 0) or 0) * 1000

        _emit_emf(
            dimension_names=["UserRole", "ToolName"],
            dimension_values={"UserRole": role, "ToolName": tool_name},
            metrics={
                "ToolCalls": (tool.get("calls", 0), "Count"),
                "ToolSuccess": (tool.get("success", 0), "Count"),
                "ToolErrors": (tool.get("errors", 0), "Count"),
                "ToolDurationMs": (duration_ms, "Milliseconds"),
            },
        )
