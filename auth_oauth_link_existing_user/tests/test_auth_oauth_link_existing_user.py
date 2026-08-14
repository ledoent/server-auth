# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import AccessDenied
from odoo.tests import TransactionCase


class TestAuthOauthLinkExistingUser(TransactionCase):
    """Most of these are refusals.

    The module widens who can sign in, so the tests that carry weight are the
    ones proving it does not widen it too far.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env.ref("auth_oauth.provider_google")
        cls.ResUsers = cls.env["res.users"]
        cls.user = cls._create_user("target@example.com", "Target User")
        cls.env["ir.config_parameter"].sudo().set_param(
            "auth_oauth_link_existing_user.allowed_domains", "example.com"
        )

    @classmethod
    def _create_user(cls, login, name):
        return cls.env["res.users"].create(
            {"name": name, "login": login, "email": login}
        )

    def _validation(self, email, verified=True, uid="oauth-uid-1"):
        return {"user_id": uid, "email": email, "email_verified": verified}

    def _link(self, validation):
        return self.ResUsers._oauth_link_existing_user(
            self.provider.id, validation, {"access_token": "token"}
        )

    # -- linking ---------------------------------------------------------- #

    def test_links_verified_allowed_address(self):
        login = self._link(self._validation("target@example.com"))
        self.assertEqual(login, self.user.login)
        self.assertEqual(self.user.oauth_uid, "oauth-uid-1")
        self.assertEqual(self.user.oauth_provider_id, self.provider)

    def test_match_is_case_insensitive(self):
        self.assertEqual(
            self._link(self._validation("TARGET@Example.COM")), self.user.login
        )

    def test_same_identity_links_again(self):
        """A second sign-in must not start failing."""
        self._link(self._validation("target@example.com"))
        self.assertEqual(
            self._link(self._validation("target@example.com")), self.user.login
        )

    def test_empty_domain_list_allows_any_verified_domain(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "auth_oauth_link_existing_user.allowed_domains", ""
        )
        other = self._create_user("someone@other.test", "Other")
        self._link(self._validation("someone@other.test", uid="uid-other"))
        self.assertEqual(other.oauth_uid, "uid-other")

    # -- refusals --------------------------------------------------------- #

    def test_refuses_unverified_address(self):
        """The safety argument rests entirely on the provider verifying it."""
        self.assertIsNone(
            self._link(self._validation("target@example.com", verified=False))
        )
        self.assertFalse(self.user.oauth_uid)

    def test_refuses_when_verified_flag_absent(self):
        """Silence is not verification."""
        validation = self._validation("target@example.com")
        del validation["email_verified"]
        self.assertIsNone(self._link(validation))
        self.assertFalse(self.user.oauth_uid)

    def test_refuses_domain_outside_the_list(self):
        outsider = self._create_user("someone@other.test", "Outsider")
        self.assertIsNone(
            self._link(self._validation("someone@other.test", uid="uid-outsider"))
        )
        self.assertFalse(outsider.oauth_uid)

    def test_refuses_rebinding_a_different_identity(self):
        """Rebinding would be an account-takeover primitive."""
        self.user.write(
            {"oauth_uid": "existing-uid", "oauth_provider_id": self.provider.id}
        )
        self.assertIsNone(
            self._link(self._validation("target@example.com", uid="attacker-uid"))
        )
        self.assertEqual(self.user.oauth_uid, "existing-uid")

    def test_refuses_archived_user(self):
        self.user.write({"active": False})
        self.assertIsNone(self._link(self._validation("target@example.com")))
        self.assertFalse(self.user.oauth_uid)

    def test_refuses_unknown_address(self):
        self.assertIsNone(self._link(self._validation("nobody@example.com")))

    def test_refuses_malformed_addresses(self):
        for value in ("", None, "   ", "not-an-email"):
            self.assertIsNone(self._link(self._validation(value)))

    # -- integration with the inherited flow ------------------------------ #

    def test_signin_raises_when_link_is_refused(self):
        """A refusal must leave behaviour identical to not installing this."""
        with self.assertRaises(AccessDenied):
            self.ResUsers._auth_oauth_signin(
                self.provider.id,
                self._validation("nobody@example.com"),
                {"access_token": "token"},
            )

    def test_signin_returns_login_when_link_succeeds(self):
        login = self.ResUsers._auth_oauth_signin(
            self.provider.id,
            self._validation("target@example.com"),
            {"access_token": "token"},
        )
        self.assertEqual(login, self.user.login)

    # -- configuration ---------------------------------------------------- #

    def test_allowed_domains_parsing(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "auth_oauth_link_existing_user.allowed_domains",
            " Example.COM , other.test ,, ",
        )
        self.assertEqual(
            self.ResUsers._oauth_link_allowed_domains(),
            {"example.com", "other.test"},
        )

    def test_setting_round_trips_through_config_settings(self):
        settings = self.env["res.config.settings"].create(
            {"auth_oauth_link_allowed_domains": "a.test,b.test"}
        )
        settings.execute()
        self.assertEqual(
            self.ResUsers._oauth_link_allowed_domains(), {"a.test", "b.test"}
        )
