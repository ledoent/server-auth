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
        # get_str, not get_param: 20.0 removed the untyped get_param/set_param
        # pair in favour of get_bool/get_int/get_float/get_str. Left as
        # get_param this raises AttributeError on every login that reaches the
        # link path -- the module's only code path -- and no upgrade_code
        # script rewrites it. The .sudo() stays: get_str still checks read
        # access.
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_str("auth_oauth_link_existing_user.allowed_domains", "")
        )
        return {d.strip().lower() for d in (param or "").split(",") if d.strip()}

    @api.model
    def _oauth_link_check_email_verified(self, provider, validation):
        """Whether the address may be treated as verified.

        Absence is still unverified by default. Providers that verify addresses
        usually say so explicitly, and inferring verification from silence is
        how an account takeover gets through.

        The exception is a provider that verifies addresses but never sends the
        claim. Microsoft Entra ID is one: its /oidc/userinfo returns sub, name
        and email, and no email_verified at all. Read strictly, that refuses
        every Entra sign-in. Read loosely -- absence means fine -- it would also
        wave through providers that let a user type their own address, which is
        the takeover case above.

        So it is neither, but a per-provider decision: off unless somebody turned
        it on for a directory that owns the mailboxes it asserts. Note that the
        setting fills silence only -- an explicit email_verified=False is still
        a refusal, however the provider is configured.
        """
        claim = validation.get("email_verified")
        if claim:
            return True
        if claim is not None:
            # Present and false. That is a denial, not silence, and the setting
            # below only exists to fill silence -- a provider that bothers to
            # say "not verified" is to be believed when it says it.
            return False

        provider_rec = self.env["auth.oauth.provider"].sudo().browse(provider)
        if provider_rec.link_assume_email_verified:
            # Logged rather than silent. This is the one path where an address
            # is trusted on configuration instead of on evidence, so an audit
            # needs to be able to find every time it happened.
            _logger.info(
                "OAuth link treating %s as verified: provider %r is configured "
                "as verifying addresses without sending the claim",
                (validation.get("email") or "").strip().lower(),
                provider_rec.name,
            )
            return True

        return False

    @api.model
    def _oauth_link_existing_user(self, provider, validation, params):
        """Bind this OAuth identity to an existing user, or return None.

        Returning None means the caller re-raises AccessDenied, so every refusal
        below leaves behaviour exactly as it is without this module installed.
        """
        email = (validation.get("email") or "").strip().lower()
        if not email or "@" not in email:
            return None

        if not self._oauth_link_check_email_verified(provider, validation):
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
