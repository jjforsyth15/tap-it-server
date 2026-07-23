# Local Development Setup

## Overview

This guide explains how to set up a local development environment for TapIt.

Following these steps will allow you to run the frontend, backend, and PostgreSQL database locally for development and testing.

---

# Prerequisites

Install the following software before beginning.

## Required Software

* Git
* Node.js (LTS)
* npm
* Python 3.12+
* PostgreSQL
* Firebase CLI (optional for hosting)
* Visual Studio Code (recommended)

---

# Clone the Repository

Clone the project.

```bash
git clone https://github.com/jjforsyth15/tap-it-web.git
```

```bash
git clone https://github.com/jjforsyth15/tap-it-server.git
```

Navigate into the project directory.

```bash
cd tap-it
```

---

# Project Structure

```text
tap-it/

├── tap-it-web/
├── tap-it-server/
```

* **tap-it-web** contains the React frontend.
* **tap-it-server** contains the FastAPI backend.

---

# Backend Setup

Navigate into the backend project.

```bash
cd tap-it-server
```

## Create a Virtual Environment

Windows

```bash
python -m venv .venv
```

Activate it.

```bash
.venv\Scripts\activate
```

macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file.

Example variables:

```text
DATABASE_URL=
SECRET_KEY=
ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=

FRONTEND_URL=
FRONTEND_URL_IP=
CURRENT_URL=
TEAM_ID=
```

Use local development values where appropriate.

Do **not** commit `.env` files.

---

## Configure PostgreSQL

Create a PostgreSQL database for local development.

Update `DATABASE_URL` to point to your local database.

---

## Run Database Migrations

```bash
alembic upgrade head
```

---

## Start the Backend

```bash
uvicorn app.main:app --reload
```

The backend will typically be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Frontend Setup

Navigate to the frontend project.

```bash
cd tap-it-web
```

Install dependencies.

```bash
npm install
```

---

## Configure Environment Variables

Create a `.env` file.

Example:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Start the Development Server

```bash
npm run dev
```

The development server will typically run at:

```text
http://localhost:5173
```

---

# Running the Application

The following services should now be running.

| Service      | URL                        |
| ------------ | -------------------------- |
| Frontend     | http://localhost:5173      |
| Backend      | http://127.0.0.1:8000      |
| Swagger Docs | http://127.0.0.1:8000/docs |

Open the frontend in your browser and begin development.

---

# Development Workflow

A typical workflow is:

1. Pull the latest changes.
2. Create a feature branch.
3. Implement changes.
4. Test locally.
5. Commit changes.
6. Push the branch.
7. Open a pull request or merge into the development branch.

---

# Useful Commands

## Frontend

Install packages

```bash
npm install
```

Start development server

```bash
npm run dev
```

Build production assets

```bash
npm run build
```

Run linter

```bash
npm run lint
```

---

## Backend

Install dependencies

```bash
pip install -r requirements.txt
```

Run development server

```bash
uvicorn app.main:app --reload
```

Run migrations

```bash
alembic upgrade head
```

Create a migration

```bash
alembic revision --autogenerate -m "Migration description"
```

---

# Troubleshooting

## Backend Will Not Start

Check:

* Virtual environment is activated
* Dependencies are installed
* `.env` file exists
* PostgreSQL is running

---

## Frontend Cannot Connect to Backend

Verify:

* Backend is running
* `VITE_API_BASE_URL` is correct
* Browser cache is cleared
* CORS configuration allows the frontend origin

---

## Database Errors

Verify:

* PostgreSQL is running
* `DATABASE_URL` is correct
* Latest migrations have been applied

---

## Missing Dependencies

If packages are missing, reinstall them.

Frontend:

```bash
npm install
```

Backend:

```bash
pip install -r requirements.txt
```

---

# Best Practices

* Keep dependencies up to date.
* Never commit secrets or `.env` files.
* Test changes locally before deploying.
* Keep migrations synchronized with model changes.
* Run the linter before committing code.
* Pull the latest changes before starting new work.

---

# Additional Resources

For more information, see:

* `README.md`
* `ARCHITECTURE.md`
* `API.md`
* `DATABASE_SCHEMA.md`
* `DEPLOYMENT.md`
