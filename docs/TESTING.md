# Testing Guide

## Overview

TapIt currently uses a primarily manual testing process supported by frontend linting, backend validation, production logging, and beta-user feedback.

This document defines the expected testing workflow for new features, bug fixes, deployments, and regression checks.

Automated testing may be added in future phases as the application grows.

---

# Testing Goals

TapIt testing focuses on:

* Verifying core user workflows
* Preventing regressions
* Confirming authorization protections
* Testing responsive behavior
* Validating error handling
* Verifying production configuration
* Confirming accessibility improvements
* Ensuring database changes behave correctly

---

# Testing Environments

Testing may be performed in the following environments:

## Local Development

Used for:

* Feature development
* Debugging
* Validation testing
* Database migration testing
* Responsive design testing

Typical local services:

| Service           | URL                          |
| ----------------- | ---------------------------- |
| Frontend          | `http://localhost:5173`      |
| Backend           | `http://127.0.0.1:8000`      |
| API Documentation | `http://127.0.0.1:8000/docs` |

## Production

Used for:

* Deployment verification
* CORS validation
* Authentication verification
* Hosted database testing
* Public profile testing
* NFC card testing
* Production logging review

Production testing should avoid creating unnecessary user accounts or data.

---

# Pre-Test Checklist

Before testing:

* Pull the latest code.
* Confirm the correct Git branch is checked out.
* Install the latest frontend and backend dependencies.
* Confirm environment variables are configured.
* Confirm PostgreSQL is running.
* Apply the latest Alembic migrations.
* Start the frontend and backend.
* Clear outdated browser data when necessary.

---

# Frontend Quality Checks

Run the frontend linter:

```bash
npm run lint
```

Run a production build:

```bash
npm run build
```

The build should complete without TypeScript errors.

Review any lint warnings before deployment and confirm they do not represent functional problems.

---

# Backend Quality Checks

Start the backend locally:

```bash
uvicorn app.main:app --reload
```

Confirm:

* The server starts successfully.
* No required environment variables are missing.
* The database connection succeeds.
* Alembic migrations are current.
* API routes load in Swagger.
* No unexpected startup warnings appear.

Optional static analysis tools may also be run when configured.

---

# Core Regression Checklist

## Authentication

### Registration

* A new user can register with valid information.
* Duplicate email addresses are rejected.
* Missing required fields are rejected.
* Invalid email formats are rejected.
* Weak or invalid passwords are rejected when applicable.
* Passwords are never returned by the API.
* A successful registration returns the expected response.
* Repeated submissions do not create duplicate users.
* Rate limiting returns `429` after too many attempts.

### Login

* A registered user can log in with valid credentials.
* Invalid credentials return an appropriate error.
* Missing fields are rejected.
* The access token is stored correctly.
* The user is redirected to the expected page.
* The `next` redirect parameter works when present.
* Too many login attempts trigger rate limiting.

### Logout

* Logout clears the stored token.
* Logout updates the authentication state.
* Protected pages become inaccessible after logout.
* The user is redirected appropriately.

### Expired Authentication

* An expired or invalid token causes protected API requests to return `401`.
* The stored token is cleared.
* The user is signed out.
* Protected routes redirect to login.
* The application does not remain in a false authenticated state.

---

# Dashboard

* The dashboard loads the authenticated user's profiles.
* An empty state appears when no profiles exist.
* The Create Profile card appears first.
* Profile cards display the correct name and status.
* Link and card counts display correctly.
* View Profile opens the correct public profile.
* Manage Profile opens the correct management page.
* Profile cards can be reordered.
* The updated order persists after refresh.
* Drag-and-drop does not prevent links and buttons from receiving keyboard focus.
* Loading and error states display appropriately.

---

# Profile Creation

* A user can create a profile with valid data.
* Profile name is required.
* Invalid profile data is rejected.
* A profile can be created without an avatar.
* A profile can be created with an avatar.
* The avatar selector works with a mouse.
* The avatar selector works using Enter or Space.
* The selected avatar has a visible focus or selection outline.
* Duplicate submissions are prevented.
* The new profile appears on the dashboard.
* Server errors display an understandable message.

---

# Profile Management

## Profile Header

* The profile name displays correctly.
* The biography displays correctly.
* The profile name can be edited.
* The biography can be edited.
* Changes persist after refresh.
* Invalid input displays an error.
* The profile status displays correctly.
* View Public Profile opens the correct profile.

## Avatar

* A valid image can be uploaded.
* The uploaded image displays correctly.
* The avatar can be replaced.
* The avatar can be removed.
* Upload controls are keyboard accessible.
* A visible focus state appears.
* Loading state appears during upload.
* Upload failures display an error.
* Repeated upload submissions are prevented.

---

# Profile Links

## Loading

* Existing links load in the correct order.
* The empty state appears when no links exist.
* Loading failures display an error.

## Adding Links

* The Add Link modal opens.
* A supported label can be selected.
* The Other option allows a custom label.
* A valid URL can be submitted.
* Invalid URLs are rejected.
* Missing labels are rejected.
* Missing URLs are rejected.
* The modal closes after success.
* Form state resets after success.
* Escape closes the modal.
* Escape resets temporary form values.
* Duplicate submissions are prevented.
* Rate limiting behaves correctly.

## Deleting Links

* The delete confirmation modal opens.
* Cancel leaves the link unchanged.
* Confirm removes the link.
* Escape closes the modal.
* The link remains deleted after refresh.
* An error appears if deletion fails.

## Reordering Links

* Links can be reordered using drag-and-drop.
* The new order persists after refresh.
* Link buttons remain usable during drag-and-drop.
* Reordering works on supported desktop and mobile layouts.

## Responsive Layout

* Link rows display correctly on desktop.
* Link rows remain compact on mobile.
* The drag selector appears beside the link information on mobile.
* Long labels and URLs do not break the layout.
* Buttons remain accessible at narrow widths.

---

# Cards

## Card Display

* Assigned cards load for the correct profile.
* Card names display correctly.
* Card codes display correctly where appropriate.
* Card status displays correctly.
* The empty state appears when no cards are assigned.

## Card Updates

* A card can be renamed.
* The new name persists after refresh.
* A card status can be changed.
* Supported statuses behave correctly:

  * Active
  * Inactive
  * Lost
  * Deactivated
  * Disabled
* Invalid status updates are rejected.
* Failed updates display an error.

## Card Assignment

* An unassigned card can be assigned to a profile.
* An assigned card shows its current profile.
* A card can be reassigned when permitted.
* Unauthorized users cannot modify another user's card.
* Invalid card codes return an appropriate error.

---

# Card Activation

* A valid unassigned card opens the activation flow.
* An authenticated user can select an existing profile.
* An authenticated user can create a profile during activation when supported.
* Activation assigns the card to the selected profile.
* Activation updates the card status correctly.
* The activated card redirects to the correct public profile.
* Already assigned cards display the correct behavior.
* Invalid card codes return a not-found state.
* Unauthorized activation attempts are rejected.
* Repeated activation submissions do not create inconsistent data.
* Rate limiting behaves correctly.

---

# Public Profiles

* A public profile loads without authentication.
* The correct profile name displays.
* The correct biography displays.
* The avatar displays when available.
* A fallback initial displays when no avatar exists.
* Links display in the correct order.
* Links open the expected destinations.
* Invalid profile IDs display a profile-not-found state.
* Inactive or unavailable profiles behave as intended.
* The page works on mobile and desktop.
* No private user data is exposed.

---

# Public Card Routes

* A valid active card resolves to the correct profile.
* An unassigned card opens the activation route.
* Card name and status are returned correctly.
* Invalid card codes display an appropriate error.
* Public card requests do not require authentication.
* Card routing works after a production deployment.
* Physical NFC scans open the expected URL.

---

# Beta Feedback

* The feedback widget opens.
* Feedback type can be selected.
* Description is required where applicable.
* Optional contact information can be submitted.
* The current page URL is recorded.
* Browser information is recorded.
* Screen size is recorded.
* Application version is recorded.
* Feedback can be submitted while logged in.
* Anonymous feedback works when permitted.
* A success message appears after submission.
* Repeated submissions are prevented.
* Rate limiting behaves correctly.
* Failed submissions display an understandable error.

---

# Authorization and Security

Verify that an authenticated user cannot:

* View private management data belonging to another user.
* Edit another user's profile.
* Delete another user's links.
* Reorder another user's links.
* Modify another user's cards.
* Upload or remove another user's avatar.
* Activate a card in an unauthorized way.

Protected endpoints should return:

* `401 Unauthorized` when authentication is missing or invalid
* `403 Forbidden` when the user is authenticated but lacks ownership

Public endpoints should expose only information intended for public viewing.

---

# Input Validation

Test valid, invalid, missing, and excessive input for:

* Registration fields
* Login fields
* Profile names
* Profile biographies
* Link labels
* Link URLs
* Card names
* Card statuses
* Feedback descriptions
* Contact information
* Uploaded images

Confirm that:

* Invalid data is rejected.
* Error messages are understandable.
* Backend validation remains authoritative.
* Unexpected fields do not bypass validation.
* Database transactions roll back after failed writes.

---

# Rate Limiting

Rate-limited endpoints should be tested to confirm:

* Normal use is allowed.
* Excessive attempts return `429 Too Many Requests`.
* The response is valid JSON.
* The application handles the response gracefully.
* Legitimate users are not blocked during ordinary use.

Current rate-limited operations may include:

* Registration
* Login
* Profile creation
* Avatar upload
* Link creation
* Card creation
* Card activation
* Feedback submission
* Analytics requests

---

# Error Handling

Trigger expected failure states and verify:

* API errors return JSON.
* Validation errors return appropriate status codes.
* Unauthorized requests return `401` or `403`.
* Missing resources return `404`.
* Rate limits return `429`.
* Unexpected server failures return `500`.
* The frontend displays a useful error message.
* Sensitive implementation details are not exposed.
* Failed database writes are rolled back.

---

# Logging

Review backend logs and confirm requests include useful diagnostic data such as:

* Request ID
* HTTP method
* Request path
* Response duration
* Client IP
* User agent
* Referrer where available

For unexpected server errors, confirm logs include enough context to investigate the problem without exposing sensitive values.

Passwords, JWT tokens, and secret environment variables should never be logged.

---

# Accessibility Testing

## Keyboard Navigation

* All interactive controls can be reached using Tab.
* Buttons can be activated using Enter or Space.
* Links receive visible focus.
* Form fields receive visible focus.
* Drag-and-drop elements do not capture unrelated controls.
* Modals can be closed with Escape.
* Keyboard focus does not become trapped unexpectedly.

## Visual Accessibility

* Focus indicators are visible.
* Text has sufficient contrast.
* Error messages are easy to identify.
* Buttons remain readable in disabled and loading states.
* Important state changes are not communicated through color alone.

## Screen Sizes

Test at minimum:

* Small mobile
* Large mobile
* Tablet
* Laptop
* Desktop

---

# Browser Testing

Test the application in currently supported browsers when possible:

* Google Chrome
* Microsoft Edge
* Mozilla Firefox
* Safari

Confirm:

* Layout remains consistent.
* Authentication storage works.
* File uploads work.
* Drag-and-drop works.
* Modals work.
* Public profile links work.
* NFC URLs open correctly on mobile devices.

---

# Database and Migration Testing

Before applying a new migration:

* Review the generated migration file.
* Confirm the migration matches the intended model changes.
* Test the migration on a local database.
* Confirm existing data remains valid.
* Test the application after upgrading.

Useful commands:

```bash
alembic upgrade head
```

Create a migration:

```bash
alembic revision --autogenerate -m "Migration description"
```

When applicable, test downgrade behavior before production deployment.

---

# Production Smoke Test

After every production deployment, perform a focused smoke test.

## Frontend

* Production site loads.
* Static assets load.
* Routes work after direct navigation.
* The latest version is visible.
* Browser console contains no critical errors.

## Backend

* API is reachable.
* Swagger documentation loads when enabled.
* Database connection succeeds.
* Logs show successful startup.
* No repeated server errors appear.

## Core Workflow

* Register or use a test account.
* Log in.
* Open the dashboard.
* Create or edit a profile.
* Add, reorder, and remove a link.
* Verify the public profile.
* Verify a public card URL.
* Submit beta feedback.
* Log out.
* Confirm protected routes are inaccessible.

## Production Configuration

* Frontend points to the production backend.
* CORS permits the production frontend origin.
* HTTPS is used.
* Production environment variables are loaded.
* No development URLs are unintentionally active.

---

# Bug Fix Verification

Every bug fix should be tested in two ways:

1. Confirm the original bug no longer occurs.
2. Confirm the fix did not break related functionality.

The test should reproduce the exact original conditions whenever possible.

Record:

* What caused the issue
* Steps used to reproduce it
* Expected behavior
* Actual behavior before the fix
* Result after the fix

---

# Beta Testing

Beta users provide real-world testing across different devices, browsers, screen sizes, and usage patterns.

Beta feedback should be reviewed for:

* Repeated bugs
* Confusing workflows
* Missing error messages
* Mobile layout problems
* Authentication issues
* NFC reliability
* Unexpected user behavior
* Feature requests

Issues should be prioritized based on:

* Severity
* Number of affected users
* Security impact
* Frequency
* Effect on core workflows

---

# Known Testing Limitations

The current process relies heavily on manual testing.

Current limitations may include:

* Limited automated frontend tests
* Limited automated backend tests
* No full end-to-end automated suite
* Manual cross-browser verification
* Manual deployment smoke testing
* Limited load and performance testing

These limitations are accepted for the current beta stage but should be revisited as TapIt grows.

---

# Future Testing Improvements

Potential future additions include:

* Backend unit tests with Pytest
* API integration tests
* React component tests
* End-to-end tests with Playwright or Cypress
* Automated accessibility checks
* Continuous integration testing
* Test database fixtures
* Automated migration testing
* Load and stress testing
* Security scanning
* Automated production health checks

---

# Testing Philosophy

TapIt testing should prioritize the workflows that matter most to users:

* Creating an account
* Managing profiles
* Managing links
* Activating and using NFC cards
* Opening public profiles
* Recovering gracefully from errors

A feature should not be considered complete until its successful behavior, failure behavior, authorization rules, responsive layout, and production behavior have been reviewed.
