Go to *Settings > General Settings > Integrations* and set **OAuth link allowed
domains** to a comma-separated list, for example:

    example.com,example.org

Only addresses in those domains may be linked to an existing user. Leaving the
field empty allows any domain the provider has verified, which is appropriate when
the OAuth provider itself is already restricted to one organisation.

The setting is stored in the system parameter
`auth_oauth_link_existing_user.allowed_domains`.
