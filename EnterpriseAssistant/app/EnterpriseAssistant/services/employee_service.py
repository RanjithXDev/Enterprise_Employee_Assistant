import boto3

_employees_table = None


def _get_employees_table():
    global _employees_table

    if _employees_table is None:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name="ap-south-1"
        )
        _employees_table = dynamodb.Table("EnterpriseEmployees")

    return _employees_table


def get_employee(employee_id: str):
    employees_table = _get_employees_table()

    response = employees_table.get_item(
        Key={
            "employee_id": employee_id
        }
    )
    return response.get("Item")


def get_employee_by_email(email: str):
    employees_table = _get_employees_table()

    email = email.strip().lower()

    response = employees_table.scan(
        FilterExpression="email = :email",
        ExpressionAttributeValues={
            ":email": email
        }
    )

    items = response.get("Items", [])
    return items[0] if items else None