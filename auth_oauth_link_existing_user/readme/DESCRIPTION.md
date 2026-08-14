Odoo matches an OAuth sign-in on the pair `(oauth_uid, oauth_provider_id)`. A user
created by hand — or by an import, or by another module — has neither, so the match
fails and Odoo falls through to signup instead. Signup then refuses, because
`auth_signup` raises when the address already belongs to a user:

    Another user is already registered using this email address.

That error is caught and re-raised as `AccessDenied`, which carries no explanation.
The result is that a pre-existing user can never sign in with OAuth, and the only
symptom is being returned to the login page. Nothing in the log says why.

This matters most where uninvited signup is disabled or restricted, because then
creating a user by hand is the *only* way to make one, and every such user is
unreachable by OAuth.

This module adds one fallback: when the lookup fails and signup declines, look for
an existing user whose login matches the verified address from the provider, and
bind the OAuth identity to it. Every refusal path leaves behaviour exactly as it is
without the module installed.
