# Architecture

## Overview

TapIt is a full-stack web application that allows users to share their professional and personal information through a single NFC card. Rather than requiring a mobile application or QR code, a user simply taps an NFC card against a compatible smartphone to instantly access their public profile.

The application is built using a modern web architecture consisting of a React frontend, a FastAPI backend, and a PostgreSQL database. Authentication is handled using JSON Web Tokens (JWT), while the frontend and backend are deployed independently to improve scalability and simplify deployment.

---

# High-Level Architecture

```
                User
                  │
                  ▼
       NFC Card / Web Browser
                  │
                  ▼
     Firebase Hosting (React Frontend)
                  │
            HTTPS REST API
                  │
                  ▼
       Render (FastAPI Backend)
                  │
                  ▼
          PostgreSQL Database
```

The frontend is responsible for rendering the user interface and communicating with the backend through a REST API. All persistent data, authentication, and business logic are handled by the backend.

---

# Technology Stack

## Frontend

* React
* TypeScript
* React Router
* CSS Modules
* Vite

Responsibilities:

* User interface
* Authentication state
* API communication
* Form validation
* Profile management
* Card management
* Public profile rendering

---

## Backend

* Python
* FastAPI
* SQLAlchemy ORM
* Pydantic
* JWT Authentication
* SlowAPI Rate Limiting

Responsibilities:

* Business logic
* Authentication
* Authorization
* Input validation
* Database access
* Card activation
* Public profile retrieval
* Logging and error handling

---

## Database

* PostgreSQL

The database stores all persistent application data including:

* Users
* Profiles
* NFC Cards
* Profile Links
* Card Tap Analytics
* Beta Feedback

---

# Frontend Architecture

The frontend follows a feature-oriented structure.

```
src/

api/
components/
context/
layours/
pages/
routes/
styles/
types/
utils/
```

## api/

Contains all communication with the backend REST API.

Each file is responsible for a specific resource (authentication, profiles, cards, etc.) while sharing common request logic through a centralized API helper.

---

## components/

Reusable UI components used throughout the application.

Examples include:

* Navigation
* Dashboard cards
* Profile management
* Public profile components
* Beta feedback
<!-- * Modals -->

---

## context/

Contains global application state.

Current contexts include:

* Authentication

This allows authentication state to be shared throughout the application without prop drilling.

---

## layouts/

So far this houses only the main layout.
This includes the main header and footer.

---

## pages/

Contains page-level components that represent application routes.

Examples include:

* Home
* Login
* Register
* Dashboard
* Profile Management
* Public Profile
* Card Activation
* Create Profile

---

## styles/

CSS Modules used to keep styles locally scoped to each component.

This approach prevents global style conflicts while making components easier to maintain.

---

## types/

Shared TypeScript interfaces and type definitions.

Using shared types ensures consistency between components and API responses.

---

## utils/

General utility functions shared throughout the application.

Examples include formatting helpers and reusable client-side logic.

---

# Backend Architecture

The backend follows a layered architecture where each directory has a specific responsibility.

```
app/

core/
db/
migrations/
models/
routes/
schemas/
services/
database.py
main.py
```

---

## models/

SQLAlchemy models representing database tables.

Each model defines:

* Database columns
* Relationships
* Constraints

---

## routers/

FastAPI route definitions.

Routers are responsible only for:

* Receiving requests
* Validating authentication
* Returning responses

Business logic is delegated to lower layers whenever possible.

---

## schemas/

Pydantic request and response models.

Schemas validate incoming data before it reaches the application logic and ensure consistent API responses.

---

## services/

Contains reusable business logic shared across multiple endpoints.

Moving business logic into services keeps route handlers concise and improves maintainability.

---

## core/

Application-wide middleware.

Current middleware includes functionality such as:

* Request logging
* Global exception handling
* CORS
* Rate limiting

---

# Authentication Flow

Protected endpoints use JWT authentication.

```
User Login
      │
      ▼
Credentials Verified
      │
      ▼
JWT Generated
      │
      ▼
Stored by Frontend
      │
      ▼
Authorization Header
      │
      ▼
Protected FastAPI Endpoint
      │
      ▼
Token Validation
      │
      ▼
Authorized Request
```

Passwords are securely hashed before storage and are never stored in plain text.

---

# Request Flow

A typical request follows the flow below.

```
React Component

↓

API Layer

↓

HTTPS Request

↓

FastAPI Router

↓

Validation

↓

Business Logic

↓

Database

↓

JSON Response

↓

React State Update

↓

UI Re-render
```

Separating each layer keeps responsibilities well defined and makes the application easier to test and maintain.

---

# Database Design

The primary entities within TapIt are:

### Users

Stores authentication information and account details.

Each user may own multiple profiles.

---

### Profiles

Stores publicly viewable profile information including:

* Name
* Bio
* Profile Image
* Status

Each profile belongs to exactly one user.

---

### Profile Links

Stores links displayed on public profiles.

Each link includes:

* Label
* URL
* Display order

Profiles may contain many links.

---

### Cards

Represents physical NFC cards.

Each card stores:

* Unique card code
* Status
* Assigned profile
* Activation information

A card may be assigned to one profile at a time.

---

### Card Taps

Records each time an NFC card is accessed.

These records provide the foundation for future analytics features.

---

### Beta Feedback

Stores user-submitted beta feedback, including optional contact information, application version, browser details, and submission status.

---

# Deployment Architecture

The frontend and backend are deployed independently.

```
GitHub
   │
   ├──────────────► Firebase Hosting
   │                    │
   │                    ▼
   │              React Frontend
   │
   └──────────────► Render
                        │
                        ▼
                 FastAPI Backend
                        │
                        ▼
                  PostgreSQL
```

Separating deployments allows frontend and backend updates to be released independently while simplifying hosting and scaling.

---

# Design Decisions

Several architectural decisions were made to improve maintainability and scalability.

## React + TypeScript

Provides strong type safety, reusable components, and an excellent developer experience for building modern user interfaces.

## FastAPI

Chosen for its high performance, automatic OpenAPI documentation, excellent typing support, and straightforward API development.

## PostgreSQL

Provides a reliable relational database with strong consistency and support for future scaling.

## JWT Authentication

Allows the frontend and backend to remain stateless while supporting secure authenticated API requests.

## CSS Modules

Encapsulates component styles, reducing unintended side effects and making styling easier to maintain.

## Separate Frontend and Backend Deployments

Independent deployments simplify continuous deployment workflows and allow each service to scale independently.

---

# Future Improvements

Planned future enhancements include:

* Administrative dashboard
* Expanded analytics and reporting
* Additional profile content types
* Public profile themes and customization
* Email verification
* Notification system
* Comprehensive automated testing
* Monitoring and observability improvements
* Additional accessibility enhancements

---

# Guiding Principles

TapIt is designed around several core engineering principles:

* Keep responsibilities separated between layers.
* Favor reusable, modular components.
* Validate all user input on the server.
* Build with scalability in mind.
* Prioritize maintainability over premature optimization.
* Continuously improve accessibility, performance, and developer experience.
