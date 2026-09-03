from strands import tool
from services.device_service import get_device_by_employee
from services.employee_service import get_employee
from services.ticket_service import create_ticket,get_ticket,update_ticket, close_ticket
import uuid



@tool
def get_device_status(employee_id: str) -> str:
    """
    Get the current device status for an employee.

    Args:
        employee_id: Unique employee identifier.
    """

    device = get_device_by_employee(employee_id)

    if not device:
        return f"No device found for employee {employee_id}."

    return (
        f"Device ID: {device['device_id']}\n"
        f"Device Type: {device['device_type']}\n"
        f"Status: {device['status']}\n"
        f"OS: {device['os']}\n"
        f"Last Seen: {device['last_seen']}"
    )


@tool
def get_employee_information(
    employee_id: str,
    requester_id: str,
) -> str:
    """
    Get employee information.

    Authorization for sensitive employee information
    must be enforced by the backend.

    Args:
        employee_id: Employee whose information is requested.
        requester_id: Authenticated requester ID.
    """

    employee = get_employee(employee_id)

    if not employee:
        return f"No employee found for employee {employee_id}."

    # Temporary authorization logic.
    # This will later be replaced with Cognito/backend authorization.
    if requester_id != employee_id:
        return (
            f"Access denied. Employee {requester_id} "
            f"is not authorized to access information for {employee_id}."
        )

    return (
        f"Employee ID: {employee['employee_id']}\n"
        f"Name: {employee['name']}\n"
        f"Email: {employee['email']}\n"
        f"Department: {employee['department']}\n"
        f"Role: {employee['role']}"
    )


@tool
def create_it_ticket(
    employee_id: str,
    title: str,
    description: str,
    requester_id: str,
) -> str:
    """
    Create an IT support ticket.

    This tool will later invoke the AgentCore Gateway/MCP
    create-ticket operation backed by AWS Lambda.

    Args:
        employee_id: Employee for whom the ticket is created.
        title: Short description of the issue.
        description: Detailed description of the issue.
        requester_id: Authenticated requester ID.
    """

    if requester_id != employee_id:
        return (
            f"Access denied. Employee {requester_id} "
            f"cannot create a ticket for employee {employee_id}."
        )

    employee = get_employee(employee_id)

    if not employee:
        return f"No employee found for employee {employee_id}."
    
    ticket_id  =f"INC-{uuid.uuid4().hex[:8].upper()}"

    ticket = create_ticket(
        ticket_id=ticket_id,
        employee_id=employee_id,
        title=title,
        description=description,
        priority="Medium",
    )
    if not ticket:
        return f"Unable to create ticket for employee {employee_id}."

    return (
        "IT ticket details:\n"
        f"Ticket ID: {ticket['ticket_id']}\n"
        f"Employee ID: {ticket['employee_id']}\n"
        f"Title: {ticket['title']}\n"
        f"Description: {ticket['description']}\n"
        f"Status: {ticket['status']}\n"
        f"Priority: {ticket['priority']}\n"
        f"Created At: {ticket['created_at']}"
    )


@tool
def get_ticket_details(
    ticket_id: str,
    requester_id: str,
) -> str:
    """
    Get details of an IT ticket.

    This operation will later use AgentCore Gateway/MCP.

    Args:
        ticket_id: Unique IT ticket identifier.
        requester_id: Authenticated requester ID.
    """

    ticket = get_ticket(ticket_id)

    if not ticket:
        return f"No ticket found for ticket ID {ticket_id}."

    if requester_id != ticket["employee_id"]:
        return (
            f"Access denied. Employee {requester_id}"
            f"is not authorized to access ticket {ticket_id}."
        )

    return (
        "IT ticket details:\n"
        f"Ticket ID: {ticket['ticket_id']}\n"
        f"Employee ID: {ticket['employee_id']}\n"
        f"Title: {ticket['title']}\n"
        f"Description: {ticket['description']}\n"
        f"Status: {ticket['status']}\n"
        f"Priority: {ticket['priority']}\n"
        f"Created At: {ticket['created_at']}"
    )


@tool
def update_it_ticket(
    ticket_id: str,
    requester_id: str,
    status: str = "",
    priority: str = "",
) -> str:
    """
    Update an existing IT ticket.

    Args:
        ticket_id: Unique IT ticket identifier.
        requester_id: Authenticated requester ID.
        status: New ticket status.
        priority: New ticket priority.
    """

    valid_statuses = {
        "Open",
        "In Progress",
        "Resolved",
        "Closed",
    }

    valid_priorities = {
        "Low",
        "Medium",
        "High",
        "Critical",
    }

    if status and status not in valid_statuses:
        return (
            f"Invalid status '{status}'. "
            f"Valid statuses are: {', '.join(valid_statuses)}."
        )

    if priority and priority not in valid_priorities:
        return (
            f"Invalid priority '{priority}'. "
            f"Valid priorities are: {', '.join(valid_priorities)}."
        )

   
    ticket = get_ticket(ticket_id)
    if not ticket:
        return f"No ticket found for ticket ID {ticket_id}"

    if requester_id != ticket['employee_id']:
        return (
            f"Access denied. Employee {requester_id}"
            f"is not authorized to update ticket {ticket_id}."
        )

    
    if not status and not priority:
        return "No ticket changes were provided."

    updated_ticket = update_ticket(
        ticket_id=ticket_id,
        status=status or None,
        priority=priority or None,
    )

    if not updated_ticket:
        return f"Unable to update ticket {ticket_id}."


    return (
        f"Ticket update request received for {ticket_id}.\n"
        f"Requester ID: {requester_id}\n"
        f"Status: {status or 'No change'}\n"
        f"Priority: {priority or 'No change'}\n"
        "Ticket update will be handled by "
        "AgentCore Gateway → MCP → Lambda."
    )

@tool
def close_it_ticket(
    ticket_id: str,
    requester_id: str,
) -> str:
    """
    Close an existing IT ticket.

    Args:
        ticket_id: Unique IT ticket identifier.
        requester_id: Authenticated requester ID.
    """
    
    ticket = get_ticket(ticket_id)

    if not ticket:
        return f"No ticket found for ticket ID {ticket_id}."

    if requester_id != ticket["employee_id"]:
        return (
            f"Access denied. Employee {requester_id} "
            f"is not authorized to close ticket {ticket_id}."
        )

    if ticket["status"] == "Closed":
        return f"Ticket {ticket_id} is already closed."

    closed_ticket = close_ticket(ticket_id)

    if not closed_ticket:
        return f"Unable to close ticket {ticket_id}."


    return (
        f"Ticket closure request received for {ticket_id}.\n"
        f"Requester ID: {requester_id}\n"
        "Ticket closure will be handled by "
        "AgentCore Gateway → MCP → Lambda."
    )