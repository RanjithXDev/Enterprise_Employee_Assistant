from strands import tool
from services.device_service import get_device_by_employee
from services.employee_service import get_employee
from services.ticket_service import (
    create_ticket,
    get_ticket,
    update_ticket,
    close_ticket,
)

from services.approval_service import create_approval
import uuid


def _is_admin(user_role: str) -> bool:
    """Return True only for the trusted ITAdmin role."""
    return user_role == "ITAdmin"


def _is_authorized(
    requester_id: str,
    resource_employee_id: str,
    user_role: str,
) -> bool:
    """
    Employees can access their own resources.
    ITAdmins can manage resources across employees.
    """

    if _is_admin(user_role):
        return True

    return requester_id == resource_employee_id


@tool
def get_device_status(
    employee_id: str,
    requester_id: str,
    user_role: str = "Employee",
) -> str:
    """
    Get the current device status for an employee.

    Employees can access their own device.
    ITAdmins can access devices for other employees.
    """

    if not _is_authorized(
        requester_id,
        employee_id,
        user_role,
    ):
        return (
            f"Access denied. Employee {requester_id} "
            f"is not authorized to access device information "
            f"for {employee_id}."
        )

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
    user_role: str = "Employee",
) -> str:
    """
    Get employee information.

    Employees can access their own information.
    ITAdmins can access employee information for support purposes.
    """

    employee = get_employee(employee_id)

    if not employee:
        return f"No employee found for employee {employee_id}."

    if not _is_authorized(
        requester_id,
        employee_id,
        user_role,
    ):
        return (
            f"Access denied. Employee {requester_id} "
            f"is not authorized to access information "
            f"for {employee_id}."
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
    user_role: str = "Employee",
) -> str:
    """
    Create an IT support ticket.

    Employees can create tickets for themselves.
    ITAdmins can create tickets for employees.
    """

    if not _is_authorized(
        requester_id,
        employee_id,
        user_role,
    ):
        return (
            f"Access denied. Employee {requester_id} "
            f"cannot create a ticket for employee {employee_id}."
        )

    employee = get_employee(employee_id)

    if not employee:
        return f"No employee found for employee {employee_id}."

    ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

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
    user_role: str = "Employee",
) -> str:
    """
    Get details of an IT ticket.

    Employees can access their own tickets.
    ITAdmins can access tickets across employees.
    """

    ticket = get_ticket(ticket_id)

    if not ticket:
        return f"No ticket found for ticket ID {ticket_id}."

    if not _is_authorized(
        requester_id,
        ticket["employee_id"],
        user_role,
    ):
        return (
            f"Access denied. Employee {requester_id} "
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
    user_role: str = "Employee",
) -> str:
    """
    Update an existing IT ticket.

    Employees can update their own tickets.
    ITAdmins can update tickets across employees.
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
        return f"No ticket found for ticket ID {ticket_id}."

    if not _is_authorized(
        requester_id,
        ticket["employee_id"],
        user_role,
    ):
        return (
            f"Access denied. Employee {requester_id} "
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
        f"Ticket {ticket_id} updated successfully.\n"
        f"Requester ID: {requester_id}\n"
        f"Status: {updated_ticket.get('status', 'Unknown')}\n"
        f"Priority: {updated_ticket.get('priority', 'Unknown')}"
    )


@tool
def close_it_ticket(
    ticket_id: str,
    requester_id: str,
    user_role: str = "Employee",
) -> str:
    """
    Request approval before closing an IT ticket.

    Employees and ITAdmins must receive approval before
    the ticket is actually closed.
    """

    ticket = get_ticket(ticket_id)

    if not ticket:
        return f"No ticket found for ticket ID {ticket_id}."

    if not _is_authorized(
        requester_id,
        ticket["employee_id"],
        user_role,
    ):
        return (
            f"Access denied. Employee {requester_id} "
            f"is not authorized to close ticket {ticket_id}."
        )

    if ticket["status"] == "Closed":
        return f"Ticket {ticket_id} is already closed."

    approval = create_approval(
        requester_id=requester_id,
        user_role=user_role,
        action="CLOSE_TICKET",
        resource_id=ticket_id,
        details={
            "employee_id": ticket["employee_id"],
            "title": ticket.get("title", ""),
            "description": ticket.get("description", ""),
            "current_status": ticket["status"],
            "priority": ticket.get("priority", ""),
        },
    )

    return (
        "PENDING_APPROVAL\n"
        f"Approval ID: {approval['approval_id']}\n"
        f"Action: Close IT ticket {ticket_id}\n"
        f"Employee ID: {ticket['employee_id']}\n"
        f"Requester ID: {requester_id}\n"
        f"User Role: {user_role}\n"
        "The ticket has NOT been closed. "
        "Human approval is required before this action can be executed."
    )