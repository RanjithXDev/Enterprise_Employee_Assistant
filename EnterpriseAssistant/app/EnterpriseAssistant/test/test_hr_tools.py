from tools.hr_tools import (
    get_hr_employee_information,
    get_employee_leave_balance,
)


def test_get_hr_employee_information():
    result = get_hr_employee_information(
        employee_id="EMP001",
        requester_id="EMP001",
    )

    assert "EMP001" in result
    assert "user1@grootan.com" in result


def test_get_employee_leave_balance():
    result = get_employee_leave_balance(
        employee_id="EMP001",
        requester_id="EMP001",
    )

    assert "EMP001" in result
    assert "Total Leave" in result
    assert "Used Leave" in result
    assert "Remaining Leave" in result


def test_hr_employee_information_denied():
    result = get_hr_employee_information(
        employee_id="EMP001",
        requester_id="EMP002",
    )

    assert "Access denied" in result


def test_leave_balance_denied():
    result = get_employee_leave_balance(
        employee_id="EMP001",
        requester_id="EMP002",
    )

    assert "Access denied" in result