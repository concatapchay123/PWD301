# Authentication Architecture

Web UI and same-origin AJAX use Flask-Login/session + CSRF. REST API clients use JWT. Authentication proves identity; resource authorization remains a separate policy step. A User suspension or auth-version change invalidates both modes. Password/token/secret values are never logged or audited.

## Trust boundaries
Browser session cookie: Secure/HttpOnly/SameSite; CSRF on state-changing web/AJAX requests. JWT: Authorization header only; no localStorage use for website AJAX.
