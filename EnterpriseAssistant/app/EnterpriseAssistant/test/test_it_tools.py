from tools.it_tools import (
    get_device_status,
    get_employee_information,
    get_ticket_details,
)


def test_get_device_status():
    result = get_device_status(
        employee_id="EMP001",
        requester_id="EMP001",
    )

    assert "LAP-1001" in result
    assert "Status" in result
    assert "OS" in result


def test_get_employee_information():
    result = get_employee_information(
        employee_id="EMP001",
        requester_id="EMP001",
    )

    assert "EMP001" in result
    assert "user1@grootan.com" in result


def test_get_ticket_details():
    result = get_ticket_details(
        ticket_id="INC-1001",
        requester_id="EMP001",
    )

    assert "INC-1001" in result
    assert "WiFi issue" in result
    assert "Status" in result


def test_employee_information_denied():
    result = get_employee_information(
        employee_id="EMP001",
        requester_id="EMP002",
    )

    assert "Access denied" in result


def test_ticket_access_denied():
    result = get_ticket_details(
        ticket_id="INC-1001",
        requester_id="EMP002",
    )

    assert "Access denied" in result