import os
from datetime import datetime, timezone
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = os.getenv(
    "CONVERSATIONS_TABLE_NAME",
    "EnterpriseAssistantConversations",
)

REGION = os.getenv("AWS_REGION", "ap-south-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


def _now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def create_conversation(
    actor_id: str,
    session_id: str,
    title: str,
) -> dict[str, Any]:
    """Create conversation metadata in DynamoDB."""

    timestamp = _now()

    item = {
        "actor_id": actor_id,
        "session_id": session_id,
        "title": title,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression=(
                "attribute_not_exists(actor_id) "
                "AND attribute_not_exists(session_id)"
            ),
        )

        return item

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            existing = get_conversation(actor_id, session_id)

            if existing:
                return existing

        raise


def get_conversation(
    actor_id: str,
    session_id: str,
) -> Optional[dict[str, Any]]:
    """Get one conversation."""

    response = table.get_item(
        Key={
            "actor_id": actor_id,
            "session_id": session_id,
        }
    )

    return response.get("Item")


def list_conversations(
    actor_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List conversations for an authenticated actor."""

    response = table.query(
        KeyConditionExpression="actor_id = :actor_id",
        ExpressionAttributeValues={
            ":actor_id": actor_id,
        },
        Limit=limit,
        ScanIndexForward=False,
    )

    conversations = response.get("Items", [])

    conversations.sort(
        key=lambda item: item.get("updated_at", ""),
        reverse=True,
    )

    return conversations


def update_conversation(
    actor_id: str,
    session_id: str,
    title: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Update conversation metadata."""

    existing = get_conversation(actor_id, session_id)

    if not existing:
        return None

    timestamp = _now()

    if title is not None:
        response = table.update_item(
            Key={
                "actor_id": actor_id,
                "session_id": session_id,
            },
            UpdateExpression=(
                "SET #title = :title, "
                "updated_at = :updated_at"
            ),
            ExpressionAttributeNames={
                "#title": "title",
            },
            ExpressionAttributeValues={
                ":title": title,
                ":updated_at": timestamp,
            },
            ReturnValues="ALL_NEW",
        )
    else:
        response = table.update_item(
            Key={
                "actor_id": actor_id,
                "session_id": session_id,
            },
            UpdateExpression="SET updated_at = :updated_at",
            ExpressionAttributeValues={
                ":updated_at": timestamp,
            },
            ReturnValues="ALL_NEW",
        )

    return response.get("Attributes")


def touch_conversation(
    actor_id: str,
    session_id: str,
) -> Optional[dict[str, Any]]:
    """Update only the last-used timestamp."""

    return update_conversation(
        actor_id=actor_id,
        session_id=session_id,
    )