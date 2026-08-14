Someone from an allowed domain signs in with their provider and gets an
account, exactly as they would without this module.

Someone from any other domain is refused with Odoo's usual "Access Denied"
message, and no user is created. The server log records the refusal and the
domain that caused it, not the address:

    OAuth sign-up refused on provider 'Google OAuth2': email domain 'example.net' is not allowed.

A provider that returns no email at all is refused too, once an allow-list is
set: a rule that cannot be evaluated is treated as a failure, not as a pass.

If *Notify on Sign-up* names anyone, each created account also queues them a
message with the new user's name, login and email, and a link to the user
form. Odoo creates these accounts from the sign-up template user, so they
arrive with no application access -- the message is the cue to set their
groups. The mail goes out with the next mail queue run rather than during the
login itself, so a slow or misconfigured mail server cannot delay or break
somebody signing in.
