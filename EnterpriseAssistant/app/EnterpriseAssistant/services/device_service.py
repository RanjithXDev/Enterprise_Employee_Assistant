import boto3


_devices_table = None


def _get_devices_table():
    global _devices_table

    if _devices_table is None:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name="ap-south-1"
        )
        _devices_table = dynamodb.Table("EnterpriseDevices")

    return _devices_table


def get_device(device_id: str):
    devices_table = _get_devices_table()

    response = devices_table.get_item(
        Key={
            "device_id": device_id
        }
    )

    return response.get("Item")


def get_device_by_employee(employee_id: str):
    devices_table = _get_devices_table()

    response = devices_table.scan(
        FilterExpression="employee_id = :employee_id",
        ExpressionAttributeValues={
            ":employee_id": employee_id
        }
    )

    devices = response.get("Items", [])

    return devices[0] if devices else None