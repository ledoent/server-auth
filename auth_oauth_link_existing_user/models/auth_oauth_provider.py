# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    link_assume_email_verified = fields.Boolean(
        string="Addresses already verified",
        default=False,
        help="Treat this provider's addresses as verified even when it sends no "
        "email_verified claim.\n\n"
        "Enable it only for a provider that owns the mailboxes it asserts. A "
        "single-tenant company directory does: the address comes from the "
        "directory, not from anything the person signing in can set. Microsoft "
        "Entra ID is the case this exists for — it never sends the claim, so "
        "without this every link attempt against it is refused.\n\n"
        "Never enable it for a provider where a user can choose their own "
        "address. There it becomes an account-takeover primitive: anyone able "
        "to claim an address could seize the user that already holds it.",
    )
