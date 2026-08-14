# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import api, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        try:
            return super()._auth_oauth_signin(provider, validation, params)
        except AccessDenied:
            # Only reached when there was no oauth_uid match AND signup declined
            # to create a user. The case worth rescuing is "a user with this
            # login already exists", which is what auth_signup refuses.
            login = self._oauth_link_existing_user(provider, validation, params)
            if login:
                return login
            raise

    @api.model
    def _oauth_link_allowed_domains(self):
        """Domains whose addresses may be linked. Empty set means no restriction."""
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_oauth_link_existing_user.allowed_domains", "")
        )
        return {d.strip().lower() for d in (param or "").split(",") if d.strip()}

    @api.model
    def _oauth_link_check_email_verified(self, validation):
        """Whether the provider asserted that it verified the address.

        Absent is treated as unverified. Providers that verify addresses say so
        explicitly; inferring verification from silence is how an account takeover
        gets through.
        """
        return bool(validation.get("email_verified"))

    @api.model
    def _oauth_link_existing_user(self, provider, validation, params):
        """Bind this OAuth identity to an existing user, or return None.

        Returning None means the caller re-raises AccessDenied, so every refusal
        below leaves behaviour exactly as it is without this module installed.
        """
        email = (validation.get("email") or "").strip().lower()
        if not email or "@" not in email:
            return None

        if not self._oauth_link_check_email_verified(validation):
            _logger.info(
                "OAuth link refused for %s: provider did not report a verified email",
                email,
            )
            return None

        allowed = self._oauth_link_allowed_domains()
        if allowed and email.rsplit("@", 1)[-1] not in allowed:
            _logger.info("OAuth link refused for %s: domain not allowed", email)
            return None

        user = (
            self.sudo()
            .with_context(active_test=False)
            .search([("login", "=ilike", email)], limit=1)
        )
        if not user:
            return None

        if user.oauth_uid and user.oauth_uid != validation["user_id"]:
            # Already bound to a different identity. Rebinding silently would be
            # an account-takeover primitive.
            _logger.warning(
                "OAuth link refused for %s: already linked to another identity",
                email,
            )
            return None

        if not user.active:
            _logger.info("OAuth link refused for %s: user is archived", email)
            return None

        user.write(
            {
                "oauth_provider_id": provider,
                "oauth_uid": validation["user_id"],
                "oauth_access_token": params.get("access_token"),
            }
        )
        _logger.info("Linked OAuth identity to existing user %s", email)
        return user.login
