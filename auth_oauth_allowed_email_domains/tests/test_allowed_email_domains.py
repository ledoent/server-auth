# Copyright 2026 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import uuid

from odoo.exceptions import AccessDenied
from odoo.tests.common import TransactionCase


class TestAllowedEmailDomains(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env.ref("auth_oauth.provider_google")
        cls.user_model = cls.env["res.users"].with_context(
            tracking_disable=True, no_reset_password=True
        )
        # Let uninvited users sign up: without it every creation path below
        # would be refused by core for a reason that has nothing to do with
        # the allow-list.
        cls.env["ir.config_parameter"].sudo().set_param(
            "auth_signup.invitation_scope", "b2c"
        )
        # An already-linked user, to prove the allow-list leaves them alone.
        cls.known_user = cls.user_model.create(
            {
                "name": "John Doe",
                "login": "john@example.net",
                "email": "john@example.net",
                "oauth_uid": "oauth_uid_johndoe",
                "oauth_provider_id": cls.provider.id,
            }
        )

    def _params(self):
        return {
            "state": json.dumps({}),
            "access_token": f"FAKE_ACCESS_TOKEN_{uuid.uuid4()}",
        }

    def _signin(self, email, user_id):
        validation = {"user_id": user_id}
        if email is not None:
            validation["email"] = email
        return (
            self.env["res.users"]
            .sudo()
            ._auth_oauth_signin(self.provider.id, validation, self._params())
        )

    def _signup(self, email):
        """Sign in with an OAuth identity Odoo has never seen before."""
        return self._signin(email, f"oauth_uid_{uuid.uuid4()}")

    def _assert_refused(self, email):
        users_before = self.env["res.users"].sudo().search_count([])
        with self.assertRaises(AccessDenied):
            self._signup(email)
        self.assertEqual(
            self.env["res.users"].sudo().search_count([]),
            users_before,
            "a refused sign-up must not leave a user behind",
        )

    # -- allow-list empty: the module stays out of the way -------------------

    def test_no_allow_list_creates_any_domain(self):
        self.assertFalse(self.provider.allowed_email_domains)
        self.assertEqual(
            self._signup("new@somewhere-else.com"), "new@somewhere-else.com"
        )

    def test_blank_allow_list_creates_any_domain(self):
        # A field holding only separators is not an allow-list.
        self.provider.allowed_email_domains = " , "
        self.assertEqual(
            self._signup("new@somewhere-else.com"), "new@somewhere-else.com"
        )

    # -- allow-list set: accounts that may be created -------------------------

    def test_allowed_domain_creates_user(self):
        self.provider.allowed_email_domains = "example.com"
        login = self._signup("jane@example.com")
        self.assertEqual(login, "jane@example.com")
        created = self.env["res.users"].sudo().search([("login", "=", login)])
        self.assertEqual(len(created), 1)
        self.assertEqual(created.oauth_provider_id, self.provider)

    def test_match_is_case_insensitive(self):
        # Core keeps the provider's casing for the login; only the allow-list
        # comparison is normalised.
        self.provider.allowed_email_domains = "Example.COM"
        self.assertEqual(self._signup("Jane@EXAMPLE.com"), "Jane@EXAMPLE.com")

    def test_separators_and_whitespace_tolerated(self):
        self.provider.allowed_email_domains = " example.org ,example.com,  "
        self.assertEqual(self._signup("jane@example.com"), "jane@example.com")

    def test_plus_addressing_accepted(self):
        self.provider.allowed_email_domains = "example.com"
        self.assertEqual(self._signup("jane+tag@example.com"), "jane+tag@example.com")

    # -- allow-list set: accounts that may not ------------------------------

    def test_disallowed_domain_refused(self):
        self.provider.allowed_email_domains = "example.com"
        self._assert_refused("jane@example.net")

    def test_subdomain_not_covered(self):
        self.provider.allowed_email_domains = "example.com"
        self._assert_refused("jane@sub.example.com")

    def test_suffix_of_allowed_domain_refused(self):
        # 'notexample.com' ends with the allowed value; matching is on the whole
        # domain, not a suffix.
        self.provider.allowed_email_domains = "example.com"
        self._assert_refused("jane@notexample.com")

    def test_missing_email_claim_refused(self):
        # Fail closed: an allow-list we cannot evaluate is a refusal.
        self.provider.allowed_email_domains = "example.com"
        self._assert_refused(None)

    def test_empty_email_claim_refused(self):
        self.provider.allowed_email_domains = "example.com"
        self._assert_refused("")

    def test_malformed_email_refused(self):
        self.provider.allowed_email_domains = "example.com"
        self._assert_refused("example.com")

    def test_email_without_local_part_refused(self):
        self.provider.allowed_email_domains = "example.com"
        self._assert_refused("@example.com")

    # -- existing users are never gated --------------------------------------

    def test_known_user_outside_allow_list_still_signs_in(self):
        # The whole point of hooking the creation path: an account that exists
        # keeps working, whatever the allow-list says about its domain.
        self.provider.allowed_email_domains = "example.com"
        login = self._signin("john@example.net", "oauth_uid_johndoe")
        self.assertEqual(login, "john@example.net")

    def test_known_user_without_email_claim_still_signs_in(self):
        self.provider.allowed_email_domains = "example.com"
        self.assertEqual(self._signin(None, "oauth_uid_johndoe"), "john@example.net")

    # -- per-provider isolation ----------------------------------------------

    def test_allow_list_is_per_provider(self):
        other_provider = self.env["auth.oauth.provider"].create(
            {
                "name": "Other provider",
                "body": "Sign in with the other provider",
                "client_id": "other-client-id",
                "auth_endpoint": "https://example.org/authorize",
                "validation_endpoint": "https://example.org/tokeninfo",
                "scope": "email",
            }
        )
        self.provider.allowed_email_domains = "example.com"
        validation = {"user_id": "oauth_uid_other", "email": "jane@example.net"}
        login = (
            self.env["res.users"]
            .sudo()
            ._auth_oauth_signin(other_provider.id, validation, self._params())
        )
        self.assertEqual(login, "jane@example.net")


class TestSignupNotification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env.ref("auth_oauth.provider_google")
        cls.env["ir.config_parameter"].sudo().set_param(
            "auth_signup.invitation_scope", "b2c"
        )
        cls.watcher = (
            cls.env["res.users"]
            .with_context(tracking_disable=True, no_reset_password=True)
            .create(
                {
                    "name": "Watcher",
                    "login": "watcher@example.com",
                    "email": "watcher@example.com",
                }
            )
        )

    def _signup(self, email):
        validation = {"user_id": f"oauth_uid_{uuid.uuid4()}", "email": email}
        params = {
            "state": json.dumps({}),
            "access_token": f"FAKE_ACCESS_TOKEN_{uuid.uuid4()}",
        }
        return (
            self.env["res.users"]
            .sudo()
            ._auth_oauth_signin(self.provider.id, validation, params)
        )

    def _mails_to_watcher(self):
        return (
            self.env["mail.mail"]
            .sudo()
            .search([("recipient_ids", "in", self.watcher.partner_id.ids)])
        )

    def test_notification_sent_on_created_user(self):
        self.provider.signup_notification_user_ids = self.watcher
        before = self._mails_to_watcher()
        login = self._signup("jane@example.com")
        new_mails = self._mails_to_watcher() - before
        self.assertEqual(len(new_mails), 1)
        self.assertIn(login, new_mails.body_html)
        self.assertIn("Google OAuth2", new_mails.subject)

    def test_no_notification_without_watchers(self):
        self.assertFalse(self.provider.signup_notification_user_ids)
        before = self._mails_to_watcher()
        self._signup("jane@example.com")
        self.assertFalse(self._mails_to_watcher() - before)

    def test_no_notification_for_known_user(self):
        self.provider.signup_notification_user_ids = self.watcher
        login = self._signup("jane@example.com")
        before = self._mails_to_watcher()
        # Sign the same identity in again: no account is created this time.
        known = self.env["res.users"].sudo().search([("login", "=", login)])
        validation = {"user_id": known.oauth_uid, "email": "jane@example.com"}
        params = {
            "state": json.dumps({}),
            "access_token": f"FAKE_ACCESS_TOKEN_{uuid.uuid4()}",
        }
        self.env["res.users"].sudo()._auth_oauth_signin(
            self.provider.id, validation, params
        )
        self.assertFalse(self._mails_to_watcher() - before)

    def test_no_notification_on_refused_signup(self):
        self.provider.signup_notification_user_ids = self.watcher
        self.provider.allowed_email_domains = "example.com"
        before = self._mails_to_watcher()
        with self.assertRaises(AccessDenied):
            self._signup("jane@example.net")
        self.assertFalse(self._mails_to_watcher() - before)
