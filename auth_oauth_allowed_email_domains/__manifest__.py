# Copyright 2026 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "OAuth Allowed Email Domains",
    "summary": "Restrict which email domains OAuth may create accounts for",
    "version": "19.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "Ledo Enterprises LLC, Odoo Community Association (OCA)",
    "maintainers": ["dnplkndll"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["auth_oauth", "mail"],
    "data": [
        "data/mail_template_data.xml",
        "views/auth_oauth_views.xml",
    ],
}
