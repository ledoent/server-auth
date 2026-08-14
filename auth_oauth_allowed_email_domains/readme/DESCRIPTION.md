Letting people sign in with a company Google (or other OAuth) account is a
convenient way to onboard: `auth_signup` on *Free sign up* means a new
colleague logs in once and has an account, with nobody provisioning it by
hand. The catch is that the provider will vouch for anyone -- with a public
provider such as Google, any `@gmail.com` address gets an account on the same
terms.

This module puts an allow-list of email domains on each OAuth provider, and
applies it to the accounts the provider is allowed to *create*. Someone from
an allowed domain is enrolled as before; someone from anywhere else is refused
before a user exists.

Users that already exist are never affected. The check runs on Odoo's
account-creation path only, so an account made deliberately outside the
allowed domains -- a contractor, a shared login, an administrator -- keeps
working after the allow-list is set.

Because Odoo builds these accounts from the sign-up template user, a freshly
created user starts with no application access. The module can therefore also
notify chosen users whenever an account is created, with a link to it, so
somebody knows to give the newcomer their groups.
