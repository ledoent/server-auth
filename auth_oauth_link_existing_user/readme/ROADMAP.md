Linking matches on `login`. Sites where the login is deliberately not the email
address would need a different lookup — `auth_oauth_login_field` covers choosing
which claim becomes the login at signup, and combining the two has not been tested.
