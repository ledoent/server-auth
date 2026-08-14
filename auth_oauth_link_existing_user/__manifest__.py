# Copyright 2026 Ledo Enterprises
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "OAuth Link Existing User",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "Ledo Enterprises, Odoo Community Association (OCA)",
    "summary": """Sign in an existing user with OAuth instead of failing""",
    "category": "Tool",
    "website": "https://github.com/OCA/server-auth",
    "depends": ["auth_oauth"],
    "data": [
        "views/res_config_settings.xml",
    ],
    "installable": True,
}
