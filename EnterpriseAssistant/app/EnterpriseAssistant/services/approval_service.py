import uuid
from datetime import datetime, timezone
from services.ticket_service import close_ticket

import boto3


_APPROVALS_TABLE = None


def _get_approvals_table():
    global _APPROVALS_TABLE

    if _APPROVALS_TABLE is None:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name="ap-south-1",
        )
        _APPROVALS_TABLE = dynamodb.Table(
            "EnterpriseAssistantApprovals"
        )

    return _APPROVALS_TABLE


def create_approval(
    requester_id: str,
    user_role: str,
    action: str,
    resource_id: str,
    details: dict | None = None,
):
    approval_id = f"APR-{uuid.uuid4().hex[:8].upper()}"

    approval = {
        "approval_id": approval_id,
        "requester_id": requester_id,
        "user_role": user_role,
        "action": action,
        "resource_id": resource_id,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }

    _get_approvals_table().put_item(
        Item=approval
    )

    return approval


def get_approval(approval_id: str):
    response = _get_approvals_table().get_item(
        Key={"approval_id": approval_id}
    )

    return response.get("Item")


def update_approval_status(
    approval_id: str,
    status: str,
):
    if status not in ("APPROVED", "REJECTED"):
        raise ValueError(
            "Approval status must be APPROVED or REJECTED"
        )

    response = _get_approvals_table().update_item(
        Key={"approval_id": approval_id},
        UpdateExpression=(
            "SET #status = :status, "
            "#resolved_at = :resolved_at"
        ),
        ExpressionAttributeNames={
            "#status": "status",
            "#resolved_at": "resolved_at",
        },
        ExpressionAttributeValues={
            ":status": status,
            ":resolved_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
        ReturnValues="ALL_NEW",
    )

    return response.get("Attributes")


def get_pending_approvals():
    response = _get_approvals_table().scan(
        FilterExpression="#status = :pending",
        ExpressionAttributeNames={
            "#status": "status",
        },
        ExpressionAttributeValues={
            ":pending": "PENDING",
        },
    )

    return response.get("Items", [])

def resolve_approval(
    approval_id: str,
    decision: str,
):
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError(
            "Decision must be APPROVED or REJECTED"
        )

    approval = get_approval(approval_id)

    if not approval:
        return {
            "success": False,
            "error": f"Approval {approval_id} not found",
        }

    if approval["status"] != "PENDING":
        return {
            "success": False,
            "error": (
                f"Approval {approval_id} has already been "
                f"resolved as {approval['status']}"
            ),
        }

    if decision == "REJECTED":
        updated_approval = update_approval_status(
            approval_id,
            "REJECTED",
        )

        return {
            "success": True,
            "approval": updated_approval,
            "action_executed": False,
            "message": (
                f"Approval {approval_id} rejected. "
                f"Ticket {approval['resource_id']} was not closed."
            ),
        }

    # APPROVED
    if approval["action"] == "CLOSE_TICKET":
        ticket_id = approval["resource_id"]

        closed_ticket = close_ticket(ticket_id)

        if not closed_ticket:
            return {
                "success": False,
                "error": (
                    f"Unable to close ticket {ticket_id}"
                ),
            }

        updated_approval = update_approval_status(
            approval_id,
            "APPROVED",
        )

        return {
            "success": True,
            "approval": updated_approval,
            "action_executed": True,
            "ticket": closed_ticket,
            "message": (
                f"Approval {approval_id} approved. "
                f"Ticket {ticket_id} has been closed."
            ),
        }

    return {
        "success": False,
        "error": (
            f"Unsupported approval action: "
            f"{approval['action']}"
        ),
    }