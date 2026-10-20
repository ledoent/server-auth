Go to *Settings > General Settings > Integrations* and set **OAuth link allowed
domains** to a comma-separated list, for example:

    example.com,example.org

Only addresses in those domains may be linked to an existing user. Leaving the
field empty allows any domain the provider has verified, which is appropriate when
the OAuth provider itself is already restricted to one organisation.

The setting is stored in the system parameter
`auth_oauth_link_existing_user.allowed_domains`.

## Providers that verify addresses but never say so

Linking requires the provider to assert `email_verified`. Some providers do
verify the address and send no such claim, and against those every link attempt
is refused, with *"provider did not report a verified email"* in the log.

**Microsoft Entra ID is the case to know about.** Its `/oidc/userinfo` returns
`sub`, `name` and `email`, and no `email_verified` at all.

For those, open *Settings > Users & Companies > OAuth Providers*, pick the
provider, and tick **Addresses already verified**, next to the validation
endpoint.

Only tick it for a provider that owns the mailboxes it asserts. A single-tenant
company directory does: the address comes from the directory, not from anything
the person signing in can set. Never tick it for a provider where a user can
choose their own address — there it becomes an account-takeover primitive, since
anyone able to claim an address could seize the user that already holds it.

The setting fills silence only. A provider that explicitly sends
`email_verified: false` is still refused however this is set, and the
allowed-domain list above still applies either way.
