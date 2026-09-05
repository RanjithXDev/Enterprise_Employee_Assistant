import boto3
from datetime import datetime, timezone


_tickets_table = None


def _get_tickets_table():
    global _tickets_table

    if _tickets_table is None:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name="ap-south-1"
        )
        _tickets_table = dynamodb.Table("EnterpriseITTickets")

    return _tickets_table


def create_ticket(
    ticket_id: str,
    employee_id: str,
    title: str,
    description: str,
    priority: str = "Medium",
):
    """
    Create a new IT ticket in DynamoDB.
    """

    tickets_table = _get_tickets_table()

    ticket = {
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "title": title,
        "description": description,
        "status": "Open",
        "priority": priority,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    tickets_table.put_item(
        Item=ticket
    )

    return ticket


def get_ticket(ticket_id: str):
    """
    Get an IT ticket from DynamoDB.
    """

    tickets_table = _get_tickets_table()

    response = tickets_table.get_item(
        Key={
            "ticket_id": ticket_id
        }
    )

    return response.get("Item")


def update_ticket(
    ticket_id: str,
    status: str | None = None,
    priority: str | None = None,
):
    """
    Update an existing IT ticket.
    """

    tickets_table = _get_tickets_table()

    update_expressions = []
    expression_attribute_names = {}
    expression_attribute_values = {}

    if status:
        update_expressions.append("#status = :status")

        expression_attribute_names["#status"] = "status"

        expression_attribute_values[":status"] = status

    if priority:
        update_expressions.append("#priority = :priority")

        expression_attribute_names["#priority"] = "priority"

        expression_attribute_values[":priority"] = priority

    if not update_expressions:
        return None

    response = tickets_table.update_item(
        Key={
            "ticket_id": ticket_id
        },
        UpdateExpression="SET " + ", ".join(update_expressions),
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )

    return response.get("Attributes")


def close_ticket(ticket_id: str):
    """
    Close an existing IT ticket.
    """

    tickets_table = _get_tickets_table()

    response = tickets_table.update_item(
        Key={
            "ticket_id": ticket_id
        },
        UpdateExpression="SET #status = :status",
        ExpressionAttributeNames={
            "#status": "status"
        },
        ExpressionAttributeValues={
            ":status": "Closed"
        },
        ReturnValues="ALL_NEW",
    )

    return response.get("Attributes")
    

def list_all_tickets():
    """
    Get all IT tickets across all employees.
    """

    tickets_table = _get_tickets_table()

    response = tickets_table.scan()

    return response.get("Items", [])


def get_tickets_by_employee(employee_id: str):
    """
    Get all IT tickets belonging to an employee.
    """

    tickets_table = _get_tickets_table()

    response = tickets_table.scan(
        FilterExpression="employee_id = :employee_id",
        ExpressionAttributeValues={
            ":employee_id": employee_id
        }
    )

    return response.get("Items", [])