"""Testes locais sem Docker e sem chamadas HTTP reais."""

from __future__ import annotations

import hashlib
import hmac
import unittest

from create_only_registration import (
    RegisteredSession,
    compute_registration_mac,
    exact_identity_matches,
    sensitive_categories_in_text,
    stable_account_snapshot,
)


class CreateOnlyRegistrationUnitTests(unittest.TestCase):
    def test_registration_mac_uses_documented_field_order(self) -> None:
        expected = hmac.new(
            b"shared-secret",
            b"nonce-value\x00alice\x00password-value\x00notadmin",
            digestmod=hashlib.sha1,
        ).hexdigest()

        actual = compute_registration_mac(
            "shared-secret",
            "nonce-value",
            "alice",
            "password-value",
            admin=False,
        )

        self.assertEqual(actual, expected)

    def test_exact_identity_requires_user_domain_and_device(self) -> None:
        session = RegisteredSession(
            user_id="@alice:poc.localhost",
            access_token="opaque-token",
            device_id="DEVICE",
        )

        self.assertTrue(
            exact_identity_matches(
                session,
                expected_user_id="@alice:poc.localhost",
                expected_device_id="DEVICE",
            )
        )
        self.assertFalse(
            exact_identity_matches(
                session,
                expected_user_id="@bob:poc.localhost",
                expected_device_id="DEVICE",
            )
        )
        self.assertFalse(
            exact_identity_matches(
                session,
                expected_user_id="@alice:poc.localhost",
                expected_device_id="OTHER",
            )
        )

    def test_log_scan_returns_categories_without_values(self) -> None:
        sensitive = {
            "password": {"opaque-password-value"},
            "access_token": {"opaque-access-token"},
        }

        categories = sensitive_categories_in_text(
            "request failed with opaque-access-token",
            sensitive,
        )

        self.assertEqual(categories, ["access_token"])
        self.assertNotIn("opaque-access-token", repr(categories))

    def test_stable_snapshot_ignores_activity_fields(self) -> None:
        account = {
            "name": "@alice:poc.localhost",
            "admin": False,
            "locked": False,
            "creation_ts": 10,
            "last_seen_ts": 20,
        }

        snapshot = stable_account_snapshot(account)

        self.assertEqual(
            snapshot,
            {
                "name": "@alice:poc.localhost",
                "admin": False,
                "locked": False,
                "creation_ts": 10,
            },
        )


if __name__ == "__main__":
    unittest.main()
