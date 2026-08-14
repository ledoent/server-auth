No action is needed after installation. The next time a user whose login matches
their verified OAuth address signs in, the identity is bound to that user and
subsequent sign-ins match directly on `oauth_uid`.

Linking is refused, and the sign-in fails exactly as it would without this module,
when any of the following hold:

- the provider did not report the address as verified (`email_verified` absent or
  false);
- the address is outside the configured domain list;
- the user is already linked to a different OAuth identity; or
- the user is archived.

Each refusal is logged with the reason.
