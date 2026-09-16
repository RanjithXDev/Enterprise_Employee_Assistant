from strands import tool
from services.device_service import get_device_by_employee, _get_devices_table
from services.employee_service import get_employee
from services.ticket_service import (
    create_ticket,
    get_ticket,
    update_ticket,
    close_ticket,
    list_all_tickets as _list_all_tickets,
    get_tickets_by_employee,
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


def build_it_tools(requester_id: str, user_role: str) -> list:
    """
    Build the IT tool set for one authenticated session.

    requester_id/user_role are bound here from the trusted application
    identity, NOT exposed as model-controlled tool arguments. A model
    that forgets to pass a role/id on a given call can no longer
    silently fall back to an unauthorized default.
    """

    @tool
    def get_device_status(employee_id: str) -> str:
        """
        Get the current device status for an employee.

        Employees can access their own device.
        ITAdmins can access devices for other employees.
        """

        if not _is_authorized(requester_id, employee_id, user_role):
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
    def get_employee_information(employee_id: str) -> str:
        """
        Get employee information.

        Employees can access their own information.
        ITAdmins can access employee information for support purposes.
        """

        employee = get_employee(employee_id)

        if not employee:
            return f"No employee found for employee {employee_id}."

        if not _is_authorized(requester_id, employee_id, user_role):
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
        title: str,
        description: str,
        employee_id: str = "",
    ) -> str:
        """
        Create an IT support ticket.

        employee_id is OPTIONAL. When omitted (or blank), the ticket is
        created for the authenticated caller automatically — Employees
        never need to supply their own employee ID to open a ticket for
        themselves. ITAdmins may pass an explicit employee_id to open a
        ticket on behalf of another employee.
        """

        target_employee_id = employee_id or requester_id

        if not _is_authorized(requester_id, target_employee_id, user_role):
            return (
                f"Access denied. Employee {requester_id} "
                f"cannot create a ticket for employee {target_employee_id}."
            )

        employee = get_employee(target_employee_id)

        if not employee:
            return f"No employee found for employee {target_employee_id}."

        ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

        ticket = create_ticket(
            ticket_id=ticket_id,
            employee_id=target_employee_id,
            title=title,
            description=description,
            priority="Medium",
        )

        if not ticket:
            return f"Unable to create ticket for employee {target_employee_id}."

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
    def get_ticket_details(ticket_id: str) -> str:
        """
        Get details of an IT ticket.

        Employees can access their own tickets.
        ITAdmins can access tickets across employees.
        """

        ticket = get_ticket(ticket_id)

        if not ticket:
            return f"No ticket found for ticket ID {ticket_id}."

        if not _is_authorized(requester_id, ticket["employee_id"], user_role):
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
    def list_my_tickets(
        employee_id: str = "",
        latest_only: bool = False,
    ) -> str:
        """
        List IT tickets belonging to an employee (not restricted to
        ITAdmin — this is the everyday "list my tickets" tool).

        employee_id is OPTIONAL. When omitted (or blank), lists the
        authenticated caller's own tickets. Employees may only list
        their own tickets; ITAdmins may pass a different employee_id to
        list another employee's tickets.

        Set latest_only=True when the user asks for only their latest/
        most recent ticket (e.g. "show my latest ticket") instead of
        the full list — this returns just the single most recently
        created ticket.
        """

        target_employee_id = employee_id or requester_id

        if not _is_authorized(requester_id, target_employee_id, user_role):
            return (
                f"Access denied. Employee {requester_id} "
                f"is not authorized to list tickets for "
                f"{target_employee_id}."
            )

        tickets = get_tickets_by_employee(target_employee_id)

        if not tickets:
            return f"No tickets found for employee {target_employee_id}."

        tickets = sorted(
            tickets,
            key=lambda t: t.get("created_at", ""),
            reverse=True,
        )

        if latest_only:
            tickets = tickets[:1]
            header = f"Latest IT ticket for employee {target_employee_id}:"
        else:
            header = (
                f"IT tickets for employee {target_employee_id} "
                f"({len(tickets)} total):"
            )

        lines = [header]

        for ticket in tickets:
            lines.append(
                f"- Ticket ID: {ticket.get('ticket_id', 'N/A')}, "
                f"Title: {ticket.get('title', 'N/A')}, "
                f"Status: {ticket.get('status', 'N/A')}, "
                f"Priority: {ticket.get('priority', 'N/A')}, "
                f"Created At: {ticket.get('created_at', 'N/A')}"
            )

        return "\n".join(lines)

    @tool
    def update_it_ticket(
        ticket_id: str,
        status: str = "",
        priority: str = "",
    ) -> str:
        """
        Update an existing IT ticket's status or priority.

        Restricted to ITAdmin users only. Employees cannot update ticket
        status or priority via chat, even for their own tickets — only
        ITAdmins may perform this operation.
        """

        if not _is_admin(user_role):
            return (
                f"Access denied. Employee {requester_id} is not "
                f"authorized to update ticket {ticket_id}. Updating "
                f"ticket status or priority is restricted to ITAdmin "
                f"users."
            )

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
    def close_it_ticket(ticket_id: str) -> str:
        """
        Request approval before closing an IT ticket (Employee
        self-service path).

        Employees can request closure of their own tickets this way;
        it routes through the external Human-in-the-Loop approval
        workflow and does NOT close the ticket immediately.

        This is NOT for ITAdmin ticket closures. ITAdmins must use
        admin_close_it_ticket instead, which closes the ticket
        immediately after an explicit in-chat confirmation rather than
        the external approval workflow.
        """

        if _is_admin(user_role):
            return (
                "This tool is for Employee self-service ticket closure "
                "requests only, which route through external approval. "
                "Use admin_close_it_ticket instead — it closes the "
                "ticket immediately after an explicit in-chat "
                "confirmation from the admin."
            )

        ticket = get_ticket(ticket_id)

        if not ticket:
            return f"No ticket found for ticket ID {ticket_id}."

        if not _is_authorized(requester_id, ticket["employee_id"], user_role):
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

    @tool
    def admin_close_it_ticket(
        ticket_id: str,
        confirmed: bool = False,
    ) -> str:
        """
        Close an IT ticket via an in-chat confirmation, restricted to
        ITAdmin users.

        This is a two-step tool:

        Step 1 — call with confirmed=False (the default) or simply omit
        it. This does NOT close the ticket. It returns the ticket's
        current details so you can show them to the admin and ask an
        explicit yes/no confirmation question in the chat (e.g. "Are
        you sure you want to close ticket INC-1001? This cannot be
        undone.").

        Step 2 — only after the admin's OWN reply in this conversation
        explicitly confirms (e.g. "yes", "confirm", "close it"), call
        this tool again with confirmed=True. This actually closes the
        ticket immediately — there is no further external approval
        step for ITAdmin closures.

        Never pass confirmed=True unless the admin explicitly confirmed
        in their own message. Never infer or assume confirmation.
        """

        if not _is_admin(user_role):
            return (
                f"Access denied. Employee {requester_id} is not "
                f"authorized to use admin_close_it_ticket. Only "
                f"ITAdmin users can close tickets this way; Employees "
                f"should use close_it_ticket instead."
            )

        ticket = get_ticket(ticket_id)

        if not ticket:
            return f"No ticket found for ticket ID {ticket_id}."

        if ticket["status"] == "Closed":
            return f"Ticket {ticket_id} is already closed."

        if not confirmed:
            return (
                "CONFIRMATION_REQUIRED\n"
                f"Ticket ID: {ticket['ticket_id']}\n"
                f"Employee ID: {ticket['employee_id']}\n"
                f"Title: {ticket.get('title', '')}\n"
                f"Current Status: {ticket['status']}\n"
                "The ticket has NOT been closed. Ask the admin to "
                "explicitly confirm in the chat before calling this "
                "tool again with confirmed=True."
            )

        updated_ticket = close_ticket(ticket_id)

        if not updated_ticket:
            return f"Unable to close ticket {ticket_id}."

        return (
            f"Ticket {ticket_id} has been closed successfully.\n"
            f"Employee ID: {ticket['employee_id']}\n"
            f"Status: {updated_ticket.get('status', 'Unknown')}"
        )

    @tool
    def list_all_devices() -> str:
        """
        List all enterprise devices.
        Only ITAdmin users are authorized to use this operation.
        """
        if not _is_admin(user_role):
            return "Access denied. Only ITAdmin users can list all devices."

        devices_table = _get_devices_table()

        response = devices_table.scan()
        devices = response.get("Items", [])

        if not devices:
            return "No devices were found."

        lines = ["Enterprise Devices:"]

        for device in devices:
            lines.append(
                f"- Device ID: {device.get('device_id', 'N/A')}, "
                f"Employee ID: {device.get('employee_id', 'N/A')}, "
                f"Type: {device.get('device_type', 'N/A')}, "
                f"Status: {device.get('status', 'N/A')}, "
                f"OS: {device.get('os', 'N/A')}"
            )

        return "\n".join(lines)

    @tool
    def list_all_tickets() -> str:
        """
        List all IT tickets across all employees.
        Only ITAdmin users are authorized to use this operation.
        """
        if not _is_admin(user_role):
            return "Access denied. Only ITAdmin users can list all tickets."

        tickets = _list_all_tickets()

        if not tickets:
            return "No tickets were found."

        lines = ["Enterprise IT Tickets:"]

        for ticket in tickets:
            lines.append(
                f"- Ticket ID: {ticket.get('ticket_id', 'N/A')}, "
                f"Employee ID: {ticket.get('employee_id', 'N/A')}, "
                f"Title: {ticket.get('title', 'N/A')}, "
                f"Status: {ticket.get('status', 'N/A')}, "
                f"Priority: {ticket.get('priority', 'N/A')}"
            )

        return "\n".join(lines)

    return [
        get_device_status,
        get_employee_information,
        create_it_ticket,
        get_ticket_details,
        list_my_tickets,
        update_it_ticket,
        close_it_ticket,
        admin_close_it_ticket,
        list_all_devices,
        list_all_tickets,
    ]
