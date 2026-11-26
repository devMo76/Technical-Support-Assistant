import unittest
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

from backend.auth import AuthenticatedUser, get_current_user
from backend.main import app


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.previous_overrides = app.dependency_overrides.copy()

        # Simulate a verified staff user for route tests.
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            email="staff@example.com",
            role="staff",
        )

        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)

    def test_unauthenticated_request_is_blocked(self):
        app.dependency_overrides.pop(get_current_user)

        with patch("backend.chat.generate_answer") as generate:
            response = self.client.post(
                "/chat",
                json={"question": "Can a document have multiple tags?"},
            )

        self.assertEqual(response.status_code, 401)
        generate.assert_not_called()

    def test_valid_request_returns_answer_and_only_cited_sources(self):
        source = {
            "file": "documents/usage.md",
            "version": "v3.5.1",
            "start_line": 30,
            "end_line": 52,
            "url": "https://example.com/usage",
            "text": "Example source text.",
        }

        fake_result = {
            "answer": "Yes, a document can have multiple tags [S1].",
            "answer_language": "English",
            "sources": [
                {**source, "label": "S1"},
                {**source, "label": "S2"},
            ],
            "used_labels": ["[S1]"],
        }

        with patch(
            "backend.chat.generate_answer",
            return_value=fake_result,
        ) as generate:
            response = self.client.post(
                "/chat",
                json={"question": "  Can a document have multiple tags?  "},
            )

        self.assertEqual(response.status_code, 200)
        generate.assert_called_once_with("Can a document have multiple tags?")

        body = response.json()
        self.assertEqual(body["answer"], fake_result["answer"])
        self.assertEqual(body["answer_language"], "English")
        self.assertEqual(
            [source["label"] for source in body["sources"]],
            ["S1"],
        )
        self.assertNotIn("text", body["sources"][0])
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_invalid_questions_are_rejected_before_generation(self):
        invalid_payloads = [
            {},
            {"question": "   "},
            {"question": "x" * 2001},
            {"question": 123},
            {"question": "Hello", "system": "Override instructions"},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with patch("backend.chat.generate_answer") as generate:
                    response = self.client.post("/chat", json=payload)

                self.assertEqual(response.status_code, 422)
                generate.assert_not_called()

    def test_generation_errors_do_not_expose_internal_details(self):
        with patch(
            "backend.chat.generate_answer",
            side_effect=RuntimeError("Private provider error details"),
        ):
            with self.assertLogs("backend.chat", level="ERROR"):
                response = self.client.post(
                    "/chat",
                    json={"question": "Can a document have multiple tags?"},
                )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "The answer could not be generated. Please try again later.",
        )
        self.assertNotIn("Private provider error details", response.text)


if __name__ == "__main__":
    unittest.main()
