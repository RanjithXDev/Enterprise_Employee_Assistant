import boto3


_leave_table = None


def _get_leave_table():
    global _leave_table

    if _leave_table is None:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name="ap-south-1",
        )
        _leave_table = dynamodb.Table("EnterpriseHRLeave")

    return _leave_table


def get_leave_balance(employee_id: str):
    """
    Get leave balance for an employee.
    """

    leave_table = _get_leave_table()

    response = leave_table.get_item(
        Key={
            "employee_id": employee_id,
        }
    )

    return response.get("Item")