# Copyright 2026 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AuthOAuthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    allowed_email_domains = fields.Char(
        help="Comma-separated list of email domains allowed to have an account "
        "created for them by this provider, for instance "
        "'example.com, example.org'. Give the domain only, without the '@'. "
        "Matching is exact and case-insensitive, so 'sub.example.com' is not "
        "covered by 'example.com'. Leave empty to accept any email domain.\n"
        "Users that already exist are never affected: this only restricts "
        "the accounts the provider is allowed to create.",
    )
    signup_notification_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="auth_oauth_provider_signup_notify_user_rel",
        column1="provider_id",
        column2="user_id",
        string="Notify on Sign-up",
        domain=[("share", "=", False)],
        help="Users warned by email whenever this provider creates an account. "
        "The message links to the new user so its groups can be set.",
    )

    def _get_allowed_email_domains(self):
        """Return the provider's allow-list as a set of normalised domains."""
        self.ensure_one()
        return {
            domain.strip().lower()
            for domain in (self.allowed_email_domains or "").split(",")
            if domain.strip()
        }
