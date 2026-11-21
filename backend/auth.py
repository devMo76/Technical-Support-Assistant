import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID

import httpx
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

Role = Literal["staff", "admin"]
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    email: str | None
    role: Role


def _settings() -> tuple[str, str]:
    load_dotenv(Path(__file__).parent / ".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        )
    return url.rstrip("/"), key


async def verify_access_token(
    token: str, *, transport: httpx.AsyncBaseTransport | None = None
) -> AuthenticatedUser:
    """Verify with Supabase Auth, then load the RLS-protected staff profile."""
    url, key = _settings()
    headers = {"apikey": key, "Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=5.0, transport=transport) as client:
            auth_response = await client.get(f"{url}/auth/v1/user", headers=headers)
            if auth_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired access token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            auth_user = auth_response.json()
            user_id = UUID(auth_user["id"])
            profile_response = await client.get(
                f"{url}/rest/v1/profiles",
                headers=headers,
                params={"id": f"eq.{user_id}", "select": "role", "limit": "1"},
            )
            profile_response.raise_for_status()
    except HTTPException:
        raise
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable.",
        ) from exc

    profiles = profile_response.json()
    if not profiles or profiles[0].get("role") not in {"staff", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account does not have staff access.",
        )

    return AuthenticatedUser(
        id=user_id,
        email=auth_user.get("email"),
        role=profiles[0]["role"],
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await verify_access_token(credentials.credentials)


def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return user


def require_owner_or_admin(target_user_id: UUID, user: AuthenticatedUser) -> None:
    if user.role != "admin" and user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another user's private records.",
        )


def require_role_change_allowed(target_user_id: UUID, user: AuthenticatedUser) -> None:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    if user.id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators cannot change their own role.",
        )
