from dataclasses import dataclass

import boto3

from services.employee_service import get_employee_by_email


COGNITO_REGION = "ap-south-1"


@dataclass(frozen=True)
class AuthenticatedUser:
    email: str
    username: str
    employee_id: str | None
    groups: list[str]

    @property
    def is_admin(self) -> bool:
        return "ITAdmin" in self.groups


cognito_client = boto3.client(
    "cognito-idp",
    region_name=COGNITO_REGION,
)


def get_authenticated_user(access_token: str) -> AuthenticatedUser:

    if not access_token:
        raise ValueError("Access token is required")

    try:
        response = cognito_client.get_user(
            AccessToken=access_token
        )

    except cognito_client.exceptions.NotAuthorizedException as exc:
        raise ValueError(
            "Invalid or expired Cognito access token"
        ) from exc

    except Exception as exc:
        raise ValueError(
            f"Unable to retrieve authenticated Cognito user: {exc}"
        ) from exc

    username = response.get("Username", "")

    attributes = {
        attribute["Name"]: attribute["Value"]
        for attribute in response.get("UserAttributes", [])
    }

    email = attributes.get("email")

    if not email:
        raise ValueError(
            "Authenticated Cognito user has no email"
        )

    groups = _get_groups_from_access_token(access_token)

    # IT Admins are not tied to an employee record for now.
    if "ITAdmin" in groups:
        return AuthenticatedUser(
            email=email,
            username=username,
            employee_id=None,
            groups=groups,
        )

    employee = get_employee_by_email(email)

    if not employee:
        raise ValueError(
            f"No employee record found for authenticated email: {email}"
        )

    employee_id = employee.get("employee_id")

    if not employee_id:
        raise ValueError(
            f"Employee record for {email} has no employee_id"
        )

    return AuthenticatedUser(
        email=email,
        username=username,
        employee_id=employee_id,
        groups=groups,
    )


def _get_groups_from_access_token(
    access_token: str,
) -> list[str]:

    import base64
    import json

    try:
        payload = access_token.split(".")[1]

        payload += "=" * (-len(payload) % 4)

        decoded = base64.urlsafe_b64decode(payload)

        claims = json.loads(decoded)

        groups = claims.get("cognito:groups", [])

        if isinstance(groups, str):
            return [groups]

        if isinstance(groups, list):
            return groups

        return []

    except (
        IndexError,
        ValueError,
        json.JSONDecodeError,
    ):
        return []