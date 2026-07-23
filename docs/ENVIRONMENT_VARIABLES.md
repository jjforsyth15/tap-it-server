# Environment Variables

## Overview

TapIt uses environment variables to store configuration values that differ between development and production environments.

Sensitive information such as secrets and database connection strings should never be committed to source control. Instead, they should be stored securely using local `.env` files during development and the hosting provider's environment variable configuration in production.

---

# Frontend Variables

The frontend uses Vite environment variables.

All frontend environment variables must begin with the `VITE_` prefix to be accessible within the application.

---

## VITE_API_BASE_URL

### Description

The base URL of the backend API.

All frontend API requests are built using this value.

### Required

Yes

### Development Example

```text id="wj0nfm"
http://127.0.0.1:8000
```

### Production Example

```text id="97t7x7"
https://your-production-backend-url.com
```

---

# Backend Variables

The backend reads configuration from environment variables during application startup.

---

## DATABASE_URL

### Description

Connection string used to connect to the PostgreSQL database.

### Required

Yes

### Example

```text id="t8sxul"
postgresql://username:password@host/database
```

---

## SECRET_KEY

### Description

Secret key used to sign JWT authentication tokens.

### Required

Yes

### Notes

* Keep this value private.
* Never commit it to source control.
* Use a long, randomly generated value.

---

## ALGORITHM

### Description

JWT signing algorithm.

### Required

Yes

### Example

```text id="wt3jau"
HS256
```

---

## ACCESS_TOKEN_EXPIRE_MINUTES

### Description

Number of minutes before JWT access tokens expire.

### Required

Yes

### Example

```text id="n9g0g0"
60
```

---

## FRONTEND_URL

### Description

Primary frontend origin allowed by the backend CORS configuration.

### Required

Yes

### Development Example

```text id="dwwup4"
http://localhost:5173
```

### Production Example

```text id="rj9mje"
https://your-production-frontend-url.com
```

---

## FRONTEND_URL_IP

### Description

Additional frontend origin permitted by the backend.

This can be useful when accessing the application through an IP address or an alternate development URL.

### Required

Optional

---

## CURRENT_URL

### Description

Current backend URL used by the application where appropriate.

### Required

Yes

---

## TEAM_ID

### Description

Application configuration value used by TapIt.

### Required

If applicable

---

# Local Development

Environment variables should be stored in a local `.env` file.

Example:

```text id="o0vhl4"
DATABASE_URL=
SECRET_KEY=
ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=

FRONTEND_URL=
FRONTEND_URL_IP=
CURRENT_URL=
TEAM_ID=
```

Frontend example:

```text id="z6w93w"
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Do not commit `.env` files to Git.

---

# Production

Production environment variables should be configured through the hosting provider.

Current deployment uses:

* Render (backend)
* Firebase Hosting (frontend)

Secrets should never be hardcoded into the application.

---

# Best Practices

* Never commit secrets to source control.
* Use different values for development and production.
* Rotate secrets if they are ever exposed.
* Keep production secrets secure.
* Use descriptive variable names.
* Remove unused variables as the application evolves.

---

# Adding a New Environment Variable

When introducing a new variable:

1. Add it to the appropriate `.env` file.
2. Configure it in the production hosting environment.
3. Document it in this file.
4. Restart the application after making changes.
5. Verify the application behaves as expected.

---

# Troubleshooting

## Environment Variable Not Found

Verify:

* The variable exists.
* The name is spelled correctly.
* The application has been restarted.
* The value is defined in the correct environment.

---

## Frontend Cannot Reach Backend

Verify:

* `VITE_API_BASE_URL` is correct.
* The backend is running.
* CORS is configured correctly.

---

## Backend Startup Fails

Verify:

* All required variables are present.
* `DATABASE_URL` is valid.
* `SECRET_KEY` has been configured.
* The database is accessible.

---

# Security Considerations

Environment variables often contain sensitive information.

To protect the application:

* Never commit `.env` files.
* Never expose secrets in frontend code.
* Store production secrets using your hosting provider.
* Rotate credentials if compromise is suspected.
* Grant access only to authorized project maintainers.

---

# Maintenance

This document should be updated whenever:

* A new environment variable is added.
* A variable is renamed.
* A variable is removed.
* Deployment configuration changes.

Keeping this document current ensures that new development environments and production deployments can be configured consistently.
