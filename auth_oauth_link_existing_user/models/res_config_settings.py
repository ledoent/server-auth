# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auth_oauth_link_allowed_domains = fields.Char(
        string="OAuth link allowed domains",
        config_parameter="auth_oauth_link_existing_user.allowed_domains",
        help="Comma-separated list of email domains whose addresses may be "
        "linked to an existing user, e.g. 'example.com,example.org'. "
        "Leave empty to allow any domain the provider has verified.",
    )
