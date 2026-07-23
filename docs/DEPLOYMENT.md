# Deployment Guide

## Overview

This document describes the deployment process for TapIt.

TapIt is deployed as three independent services:

* React frontend hosted on Firebase Hosting
* FastAPI backend hosted on Render
* PostgreSQL database hosted on Supabase

Keeping these services separate allows the frontend and backend to be deployed independently while simplifying future scaling and maintenance.

---

# Production Architecture

```text
                Users
                   │
                   ▼
        Firebase Hosting
        (React + TypeScript)
                   │
             HTTPS Requests
                   │
                   ▼
          Render Web Service
        (FastAPI Backend API)
                   │
                   ▼
        Supabase PostgreSQL Database
```

The frontend communicates exclusively with the backend through HTTPS REST API requests.

The backend is responsible for authentication, business logic, validation, and database access.

---

# Prerequisites

Before deploying, ensure the following are available:

* GitHub repository
* Firebase project
* Render account
* PostgreSQL database
* Python
* Node.js
* Firebase CLI
* Git

---

# Branch Strategy

TapIt uses Git for version control.

Typical workflow:

```text
Feature Branch
        │
        ▼
Develop Branch
        │
        ▼
Main Branch
        │
        ▼
Production Deployment
```

Only stable code should be merged into the production branch.

---

# Backend Deployment

The backend is hosted as a Render Web Service.

## Build Process

Render installs project dependencies during deployment.

Typical build process:

```bash
pip install -r requirements.txt
```

Database migrations should be applied before running the latest application version.

```bash
alembic upgrade head
```

---

## Start Process

The FastAPI application is started using Uvicorn.

Typical command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render automatically supplies the production port.

---

## Environment Variables

The backend relies on environment variables for configuration.

Examples include:

| Variable                    | Purpose                            |
| --------------------------- | ---------------------------------- |
| DATABASE_URL                | PostgreSQL connection              |
| SECRET_KEY                  | JWT signing                        |
| ALGORITHM                   | JWT algorithm                      |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiration                   |
| FRONTEND_URL                | Production frontend origin         |
| FRONTEND_URL_IP             | Additional allowed frontend origin |
| CURRENT_URL                 | Current backend URL                |
| TEAM_ID                     | Application configuration          |

Sensitive values should never be committed to source control.

---

# Database Deployment

TapIt uses a managed PostgreSQL database hosted on Supabase.

The backend connects using the `DATABASE_URL` environment variable.

Schema updates are managed through Alembic migrations.

Typical migration command:

```bash
alembic upgrade head
```

---

# Frontend Deployment

The frontend is deployed using Firebase Hosting.

## Production Environment Variables

The frontend uses environment variables to determine the backend API location.

Example:

```text
VITE_API_BASE_URL
```

The production value should always point to the deployed backend service.

---

## Build

Generate a production build.

```bash
npm run build
```

Vite outputs the optimized production assets into the `dist` directory.

---

## Deploy

Deploy the frontend using Firebase Hosting.

```bash
firebase deploy
```

After deployment, Firebase automatically serves the latest production build.

---

# CORS Configuration

The backend is configured to allow requests from approved frontend origins.

Typical allowed origins include:

* Production frontend
* Local development
* Additional approved deployment URLs

Whenever the frontend domain changes, the backend CORS configuration must also be updated.

---

# Deployment Checklist

Before deployment:

* Pull latest changes
* Verify environment variables
* Run frontend build
* Verify backend starts locally
* Run database migrations
* Commit and push changes

After deployment:

* Verify frontend loads
* Verify backend health
* Test registration
* Test login
* Test protected routes
* Test public profile pages
* Test NFC card activation
* Verify image uploads
* Verify feedback submission
* Review application logs

---

# Updating an Existing Deployment

When deploying updates:

1. Merge completed work into the deployment branch.
2. Push changes to GitHub.
3. Deploy the backend if backend changes were made.
4. Run any required database migrations.
5. Deploy the frontend.
6. Perform a production smoke test.

Backend and frontend may be deployed independently when appropriate.

---

# Troubleshooting

## Frontend Cannot Reach Backend

Verify:

* `VITE_API_BASE_URL`
* Backend URL
* Backend deployment status

---

## CORS Errors

Verify:

* Backend CORS configuration
* Frontend origin
* Environment variables
* Browser cache

---

## Authentication Issues

Verify:

* JWT configuration
* Secret key
* Token expiration
* Authorization header

---

## Database Connection Errors

Verify:

* `DATABASE_URL`
* Database availability
* Applied migrations

---

## Static Site Displays Old Version

Verify:

* Frontend build completed successfully
* Firebase deployment succeeded
* Browser cache has been cleared

---

# Rollback Strategy

If a deployment introduces unexpected issues:

1. Identify the last known stable commit.
2. Redeploy that version.
3. Restore the previous frontend build if necessary.
4. Revert any incompatible database migration if required.
5. Verify application functionality before reopening production.

---

# Security Considerations

Production deployments should follow these practices:

* Never commit secrets.
* Store sensitive configuration in environment variables.
* Restrict CORS origins.
* Use HTTPS exclusively.
* Rotate secrets when necessary.
* Keep dependencies up to date.
* Monitor application logs.
* Apply database migrations carefully.

---

# Monitoring

Production deployments should be monitored for:

* Application errors
* Failed authentication attempts
* Rate limit violations
* Database connectivity
* Unexpected exceptions
* Service availability

Logging and global exception handling help identify production issues quickly.

---

# Future Improvements

Potential deployment enhancements include:

* Automated CI/CD pipelines
* Automated testing before deployment
* Zero-downtime deployments
* Health check endpoints
* Automatic rollback support
* Monitoring dashboards
* Performance metrics
* Infrastructure as Code

---

# Deployment Philosophy

TapIt's deployment strategy emphasizes:

* Independent frontend and backend deployments
* Secure configuration through environment variables
* Version-controlled database migrations
* Reliable production monitoring
* Repeatable deployment procedures
* Scalability for future growth
