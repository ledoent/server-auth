Sign-up has to be open for any of this to apply: *Settings \> General Settings
\> Permissions \> Customer Account* must be **Free sign up**. On *On
invitation* Odoo never creates an account for an unknown OAuth identity, so
the allow-list has nothing to act on.

Then, with the developer mode active, go to *Settings \> Users & Companies \>
OAuth Providers* and open the provider you want to restrict.

**Allowed Email Domains** takes a comma-separated list of domains:

    example.com, example.org

- Give the domain only, without the `@`.
- Matching is on the whole domain and is case-insensitive. `example.com` does
  **not** cover `sub.example.com`; list the subdomain too if you need it.
- Leave the field empty to let the provider create an account for any email
  domain, which is Odoo's standard behaviour.

**Notify on Sign-up** takes the internal users who should hear about each
account the provider creates. Leave it empty to send nothing.

Both settings are per provider: restricting Google does not restrict the
others.
