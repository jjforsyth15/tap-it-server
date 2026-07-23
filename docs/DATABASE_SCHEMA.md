# Database Schema

## Overview

TapIt uses a PostgreSQL relational database to store user accounts, public profiles, NFC card assignments, profile links, analytics, and beta feedback.

The database is designed around normalized relationships, ensuring data integrity while allowing users to manage multiple profiles and NFC cards.

Primary keys are stored as UUIDs to provide globally unique identifiers and reduce predictability compared to sequential IDs.

---

# Entity Relationship Overview

```text
Users
│
├── Profiles
│     ├── Profile Links
│     └── Cards
│            └── Card Taps
│
└── Beta Feedback
```

A single user may own multiple profiles.

Each profile may contain multiple links and multiple NFC cards.

Each card may generate multiple tap events for future analytics.

Beta feedback may optionally be associated with a registered user.

---

# Tables

## Users

Stores authentication and account information.

### Purpose

Represents an individual TapIt account.

### Primary Key

* `user_id`

### Important Fields

* Email
* Password hash
* First name
* Last name
* Email verification status
* Phone number
* Account status
* Created timestamp
* Updated timestamp

### Relationships

* One-to-many with Profiles
* One-to-many with Beta Feedback

---

## Profiles

Stores publicly viewable profile information.

Each user may create multiple profiles for different purposes (for example, personal, professional, or portfolio profiles).

### Primary Key

* `profile_id`

### Foreign Keys

* `user_id`

### Important Fields

* Profile name
* Bio
* Profile image URL
* Profile status
* Display order
* Created timestamp
* Updated timestamp

### Relationships

* Belongs to one User
* One-to-many with Profile Links
* One-to-many with Cards

---

## Profile Links

Stores links displayed on public profiles.

Each link represents a destination such as LinkedIn, GitHub, a portfolio website, or another supported platform.

### Primary Key

* `link_id`

### Foreign Keys

* `profile_id`

### Important Fields

* Link label
* URL
* Display order
* Created timestamp
* Updated timestamp

### Relationships

* Belongs to one Profile

---

## Cards

Represents physical NFC cards.

Cards may exist before activation and can later be assigned to a profile.

### Primary Key

* `card_id`

### Foreign Keys

* `profile_id` (nullable)

### Important Fields

* Card code
* Card name
* Card status
* Pointing URL
* Activation timestamp
* Created timestamp
* Updated timestamp

### Relationships

* Belongs to one Profile (optional)
* One-to-many with Card Taps

---

## Card Taps

Records every interaction with an NFC card.

Each tap represents a visit initiated by scanning a physical card.

These records provide the foundation for future analytics and reporting features.

### Primary Key

* `tap_id`

### Foreign Keys

* `card_id`

### Important Fields

* Created timestamp

### Relationships

* Belongs to one Card

---

## Beta Feedback

Stores feedback submitted by beta testers.

Feedback may be associated with a registered user or submitted anonymously.

### Primary Key

* `feedback_id`

### Foreign Keys

* `user_id` (nullable)

### Important Fields

* Feedback type
* Description
* Contact information
* Browser information
* Screen size
* Page URL
* Application version
* Feedback status
* Created timestamp

### Relationships

* Optionally belongs to one User

---

# Relationships

The database uses foreign keys to maintain referential integrity between related records.

| Parent   | Child         | Relationship |
| -------- | ------------- | ------------ |
| Users    | Profiles      | One-to-Many  |
| Users    | Beta Feedback | One-to-Many  |
| Profiles | Profile Links | One-to-Many  |
| Profiles | Cards         | One-to-Many  |
| Cards    | Card Taps     | One-to-Many  |

Ownership validation within the backend ensures authenticated users may only modify resources they own.

---

# UUID Primary Keys

All primary entities use UUIDs instead of auto-incrementing integers.

Benefits include:

* Globally unique identifiers
* Reduced predictability
* Easier distributed scaling
* Safer exposure through public APIs

---

# Ordering

Several entities include a `display_order` field.

This allows the frontend to preserve user-defined ordering without recalculating positions during rendering.

Current ordered entities include:

* Profiles
* Profile Links

---

# Status Enums

Several tables use enumerated values to enforce valid states.

Examples include:

### Profile Status

* Active
* Inactive

### Card Status

* Active
* Inactive
* Lost
* Deactivated
* Disabled

### Feedback Status

* Open
* In Progress
* Resolved

Using enums helps maintain consistent application behavior while preventing invalid values from being stored.

---

# Timestamps

Most tables include timestamps for auditing and future analytics.

Common timestamp fields include:

* Created At
* Updated At

Cards additionally store:

* Activated At

These timestamps provide a historical record of user activity and resource changes.

---

# Data Integrity

The database is designed to maintain consistency through several mechanisms:

* Primary keys
* Foreign keys
* Unique constraints
* Enum validation
* Nullable relationships where appropriate
* Server-side ownership validation
* Transaction rollback on failures

These safeguards help prevent invalid or inconsistent data from being stored.

---

# Migrations

Database schema changes are managed using Alembic migrations.

Each migration represents a versioned change to the schema, allowing development and production environments to remain synchronized.

Migration responsibilities include:

* Creating new tables
* Modifying existing tables
* Adding indexes
* Updating constraints
* Schema evolution over time

---

# Future Improvements

The current schema is designed to support future expansion without significant restructuring.

Planned additions may include:

* Administrative users and roles
* Tap analytics aggregation
* Public profile themes
* Additional profile content types
* Notification history
* Email verification records
* API usage analytics
* Audit logging

---

# Design Principles

The TapIt database is designed around several guiding principles:

* Normalize related data while avoiding unnecessary complexity.
* Enforce referential integrity through foreign keys.
* Keep entities focused on a single responsibility.
* Support future scalability through UUID-based identifiers.
* Preserve user-defined ordering where appropriate.
* Maintain consistency through validation, constraints, and transactions.
* Provide a flexible foundation for future platform growth.
