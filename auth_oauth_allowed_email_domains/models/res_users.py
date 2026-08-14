# Copyright 2026 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, models
from odoo.exceptions import AccessDenied
from odoo.fields import Command

_logger = logging.getLogger(__name__)

NOTIFICATION_TEMPLATE = (
    "auth_oauth_allowed_email_domains.mail_template_oauth_signup_notification"
)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        # Core only reaches this when the OAuth identity matched no user, so
        # hooking here restricts account *creation* and leaves everybody who
        # already has an account alone -- including the ones deliberately
        # created outside the allowed domains.
        self._check_oauth_allowed_email_domain(provider, validation)
        return super()._generate_signup_values(provider, validation, params)

    @api.model
    def _check_oauth_allowed_email_domain(self, provider, validation):
        """Refuse to create an account whose email is outside the allow-list."""
        oauth_provider = self.env["auth.oauth.provider"].sudo().browse(provider)
        allowed_domains = oauth_provider._get_allowed_email_domains()
        if not allowed_domains:
            return
        email = (validation.get("email") or "").strip().lower()
        local_part, separator, domain = email.rpartition("@")
        if local_part and separator and domain in allowed_domains:
            return
        # The provider vouched for an identity we are not willing to enrol.
        # Log the domain rather than the address: enough to diagnose a
        # misconfigured allow-list without writing user emails to the log.
        _logger.info(
            "OAuth sign-up refused on provider %r: email domain %r is not allowed.",
            oauth_provider.name,
            domain,
        )
        raise AccessDenied()

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        oauth_uid = validation.get("user_id")
        known = bool(oauth_uid) and bool(
            self.sudo().search_count(
                [("oauth_uid", "=", oauth_uid), ("oauth_provider_id", "=", provider)],
                limit=1,
            )
        )
        login = super()._auth_oauth_signin(provider, validation, params)
        if login and not known:
            self.sudo().search([("login", "=", login)], limit=1)._notify_oauth_signup()
        return login

    def _notify_oauth_signup(self):
        """Warn the provider's watchers that this account was just created."""
        for user in self:
            partners = user.oauth_provider_id.sudo().signup_notification_user_ids
            partners = partners.partner_id.filtered("email")
            if not partners:
                continue
            template = self.env.ref(NOTIFICATION_TEMPLATE, raise_if_not_found=False)
            if not template:
                continue
            try:
                # Queued rather than sent inline: a slow or misconfigured mail
                # server must not delay a login, and must never fail one.
                template.sudo().send_mail(
                    user.id,
                    force_send=False,
                    email_values={"recipient_ids": [Command.set(partners.ids)]},
                )
            except Exception:  # noqa: BLE001 - a login must survive a bad template
                _logger.exception(
                    "Could not queue the sign-up notification for user %r.", user.login
                )
