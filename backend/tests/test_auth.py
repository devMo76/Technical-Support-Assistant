import os
import unittest
from unittest.mock import patch
from uuid import UUID

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.auth import (
    AuthenticatedUser,
    get_current_user,
    require_admin,
    require_owner_or_admin,
    require_role_change_allowed,
    verify_access_token,
)
from backend.main import app

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_ID = UUID("22222222-2222-2222-2222-222222222222")


def supabase_transport(auth_status: int, *, role: str = "staff"):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/v1/user":
            if auth_status != 200:
                return httpx.Response(auth_status, json={"message": "invalid token"})
            return httpx.Response(
                200, json={"id": str(USER_ID), "email": "staff@example.com"}
            )
        if request.url.path == "/rest/v1/profiles":
            return httpx.Response(200, json=[{"role": role}])
        return httpx.Response(404)

    return httpx.MockTransport(handler)


class TokenVerificationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://project.example",
                "SUPABASE_PUBLISHABLE_KEY": "test-key",
            },
        )
        self.environment.start()

    async def asyncTearDown(self):
        self.environment.stop()

    async def test_verified_token_returns_staff_profile(self):
        user = await verify_access_token(
            "valid", transport=supabase_transport(200, role="staff")
        )
        self.assertEqual(user.id, USER_ID)
        self.assertEqual(user.role, "staff")

    async def test_invalid_token_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            await verify_access_token("invalid", transport=supabase_transport(401))
        self.assertEqual(context.exception.status_code, 401)

    async def test_expired_token_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            await verify_access_token("expired", transport=supabase_transport(401))
        self.assertEqual(context.exception.status_code, 401)


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.staff = AuthenticatedUser(USER_ID, "staff@example.com", "staff")
        self.admin = AuthenticatedUser(USER_ID, "admin@example.com", "admin")

    def test_missing_token_is_rejected(self):
        response = TestClient(app).get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_staff_is_denied_admin_access(self):
        with self.assertRaises(HTTPException) as context:
            require_admin(self.staff)
        self.assertEqual(context.exception.status_code, 403)

    def test_staff_is_denied_admin_endpoint(self):
        app.dependency_overrides[get_current_user] = lambda: self.staff
        try:
            response = TestClient(app).get("/admin/check")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 403)

    def test_staff_is_denied_cross_user_access(self):
        with self.assertRaises(HTTPException) as context:
            require_owner_or_admin(OTHER_ID, self.staff)
        self.assertEqual(context.exception.status_code, 403)

    def test_owner_and_admin_are_allowed(self):
        require_owner_or_admin(USER_ID, self.staff)
        require_owner_or_admin(OTHER_ID, self.admin)

    def test_user_cannot_change_own_role(self):
        with self.assertRaises(HTTPException) as context:
            require_role_change_allowed(USER_ID, self.admin)
        self.assertEqual(context.exception.status_code, 403)

    def test_staff_cannot_change_roles(self):
        with self.assertRaises(HTTPException) as context:
            require_role_change_allowed(OTHER_ID, self.staff)
        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
