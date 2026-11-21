from secrets import compare_digest
from typing import Optional

from fastapi import Header, HTTPException, status

from backend.app.config import settings


def _tokens_match(supplied_token: str, expected_token: str) -> bool:
    return compare_digest(
        supplied_token.encode("utf-8"),
        expected_token.encode("utf-8"),
    )


def require_application_access(
    x_api_token: Optional[str] = Header(default=None, alias="X-API-Token"),
) -> None:
    expected_token = settings.APP_API_TOKEN
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application API access is not configured.",
        )
    if x_api_token is None or not _tokens_match(x_api_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid application access token is required.",
        )


def require_admin_access(
    x_admin_access_token: Optional[str] = Header(
        default=None,
        alias="X-Admin-Access-Token",
    ),
) -> None:
    expected_token = settings.ADMIN_ACCESS_TOKEN
    if (
        not expected_token
        or not settings.APP_API_TOKEN
        or _tokens_match(expected_token, settings.APP_API_TOKEN)
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrative API access is not configured.",
        )
    if (
        x_admin_access_token is None
        or not _tokens_match(x_admin_access_token, expected_token)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid administrative access token is required.",
        )
