from strands import tool

from services.employee_service import get_employee
from services.leave_service import get_leave_balance


def build_hr_tools(requester_id: str) -> list:
    """
    Build the HR tool set for one authenticated session.

    requester_id is bound here from the trusted application identity,
    NOT exposed as a model-controlled tool argument, so a model can
    never substitute a different requester when calling these tools.
    """

    @tool
    def get_hr_employee_information(employee_id: str) -> str:
        """
        Get employee information for an authorized requester.

        Args:
            employee_id: Employee whose information is requested.
        """

        employee = get_employee(employee_id)

        if not employee:
            return f"No employee found for employee {employee_id}."

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
    def get_employee_leave_balance(employee_id: str) -> str:
        """
        Get the leave balance for an employee.

        Args:
            employee_id: Employee whose leave balance is requested.
        """

        if requester_id != employee_id:
            return (
                f"Access denied. Employee {requester_id} "
                f"is not authorized to access leave information "
                f"for {employee_id}."
            )

        employee = get_employee(employee_id)

        if not employee:
            return f"No employee found for employee {employee_id}."

        leave = get_leave_balance(employee_id)

        if not leave:
            return (
                f"No leave information found for employee "
                f"{employee_id}."
            )

        return (
            f"Employee ID: {employee_id}\n"
            f"Total Leave: {leave.get('total_leave', 0)} days\n"
            f"Used Leave: {leave.get('used_leave', 0)} days\n"
            f"Remaining Leave: {leave.get('leave_balance', 0)} days"
        )

    return [
        get_hr_employee_information,
        get_employee_leave_balance,
    ]
