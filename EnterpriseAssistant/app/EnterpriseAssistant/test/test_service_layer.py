from services.employee_service import (
    get_employee,
    get_employee_by_email,
)
from services.device_service import (
    get_device,
    get_device_by_employee,
)
from services.ticket_service import (
    get_ticket,
    get_tickets_by_employee,
)
from services.leave_service import (
    get_leave_balance,
)


print("\n=== EMPLOYEE SERVICE ===")

employee = get_employee("EMP001")
print("get_employee:", employee)

employee_by_email = get_employee_by_email("user1@grootan.com")
print("get_employee_by_email:", employee_by_email)


print("\n=== DEVICE SERVICE ===")

device = get_device("LAP-1001")
print("get_device:", device)

employee_device = get_device_by_employee("EMP001")
print("get_device_by_employee:", employee_device)


print("\n=== TICKET SERVICE ===")

ticket = get_ticket("INC-1001")
print("get_ticket:", ticket)

employee_tickets = get_tickets_by_employee("EMP001")
print("get_tickets_by_employee:", employee_tickets)


print("\n=== LEAVE SERVICE ===")

leave = get_leave_balance("EMP001")
print("get_leave_balance:", leave)


print("\n=== SERVICE TEST COMPLETE ===")