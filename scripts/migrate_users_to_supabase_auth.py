"""Bulk-migrates existing local password accounts into Supabase Auth.

Written and reviewed as part of the Supabase Auth backend-readiness work
(see tap-it-vault Decisions) -- NOT run as part of that work. Running this
against production is a separate, later decision, and even then should
start with a single known test account (--email), confirming a real
Supabase sign-in works with that account's real password, before trusting
a full run.

Candidates are local users with a password_hash and no supabase_auth_id
yet, so a rerun automatically skips anyone already migrated.

Requires DATABASE_URL_DIRECT (same as the rest of the app) -- loaded from
.env automatically, no manual export needed. Self-contained: does not
import the app package, so no PYTHONPATH/-m setup is required either.

Usage, from the tap-it-server repository root:
    python scripts/migrate_users_to_supabase_auth.py --dry-run
    python scripts/migrate_users_to_supabase_auth.py --email someone@example.com
    python scripts/migrate_users_to_supabase_auth.py
Exits with status 1 if any row failed to migrate, 0 otherwise.
"""

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL_DIRECT")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL_DIRECT is not set -- check your .env file.")

# hide_parameters=True keeps bound values (encrypted_password included) out
# of any logged statement/exception text -- a dedicated engine rather than
# reusing app.database's, so this doesn't change logging behavior anywhere
# else in the app.
engine = create_engine(DATABASE_URL, hide_parameters=True)

SELECT_CANDIDATES_BASE = """
    SELECT user_id, email, password_hash, first_name, last_name, is_verified
    FROM users
    WHERE password_hash IS NOT NULL AND supabase_auth_id IS NULL
"""

# instance_id is a fixed all-zero UUID on every Supabase project (confirmed
# against a real GoTrue-created row). confirmed_at is a generated column
# (LEAST(email_confirmed_at, phone_confirmed_at)) and must never be set
# directly -- Postgres rejects writes to it.
INSERT_AUTH_USER = text(
    """
    INSERT INTO auth.users (
        instance_id, id, aud, role, email, encrypted_password,
        email_confirmed_at, confirmation_token, recovery_token,
        email_change_token_new, email_change, email_change_token_current,
        phone_change, phone_change_token, reauthentication_token,
        email_change_confirm_status, raw_app_meta_data, raw_user_meta_data,
        is_sso_user, is_anonymous, created_at, updated_at
    ) VALUES (
        '00000000-0000-0000-0000-000000000000', :auth_id, 'authenticated',
        'authenticated', :email, :encrypted_password, :email_confirmed_at,
        '', '', '', '', '', '', '', '', 0,
        '{"provider": "email", "providers": ["email"]}',
        :raw_user_meta_data, false, false, now(), now()
    )
    """
)

UPDATE_LOCAL_USER = text(
    "UPDATE users SET supabase_auth_id = :auth_id WHERE user_id = :user_id"
)


def fetch_candidates(target_email: str | None):
    query = SELECT_CANDIDATES_BASE
    params = {}
    if target_email is not None:
        query += " AND lower(email) = lower(:target_email)"
        params["target_email"] = target_email
    query += " ORDER BY created_at"

    with engine.connect() as conn:
        return conn.execute(text(query), params).fetchall()


def migrate_one(conn, row) -> uuid.UUID:
    auth_id = uuid.uuid4()
    email_confirmed_at = datetime.now(timezone.utc) if row.is_verified else None
    raw_user_meta_data = json.dumps(
        {
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email_verified": bool(row.is_verified),
        }
    )

    conn.execute(
        INSERT_AUTH_USER,
        {
            "auth_id": auth_id,
            "email": row.email,
            # Copied verbatim -- never re-hash. Double-hashing permanently
            # breaks the account's ability to sign in.
            "encrypted_password": row.password_hash,
            "email_confirmed_at": email_confirmed_at,
            "raw_user_meta_data": raw_user_meta_data,
        },
    )
    conn.execute(UPDATE_LOCAL_USER, {"auth_id": auth_id, "user_id": row.user_id})
    return auth_id


def main(dry_run: bool, limit: int | None, target_email: str | None) -> int:
    candidates = fetch_candidates(target_email)
    if limit is not None:
        candidates = candidates[:limit]

    if target_email is not None and not candidates:
        logger.error("no eligible candidate found for email=%s", target_email)
        return 1

    logger.info("found %d candidate(s) to migrate", len(candidates))

    migrated, failed = 0, 0
    for row in candidates:
        if dry_run:
            logger.info("[dry-run] would migrate user_id=%s email=%s", row.user_id, row.email)
            migrated += 1
            continue

        try:
            # engine.begin() opens its own fresh connection and transaction
            # per row, committing on success or rolling back on exception --
            # so one row's failure can never affect any other row.
            with engine.begin() as conn:
                migrate_one(conn, row)
            migrated += 1
        except Exception as e:
            failed += 1
            # Never log the raw exception or traceback here: Postgres embeds
            # the full failing row (encrypted_password included) in some
            # constraint-violation DETAIL text, independent of
            # hide_parameters -- which only hides SQLAlchemy's own parameter
            # list, not the driver's native error message. Only these three
            # explicitly-chosen fields are safe.
            sqlstate = getattr(getattr(e, "orig", None), "sqlstate", None)
            logger.error(
                "failed to migrate user_id=%s exception_type=%s sqlstate=%s",
                row.user_id,
                type(e).__name__,
                sqlstate,
            )

    logger.info("done: migrated=%d failed=%d", migrated, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="log candidates without writing anything"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="migrate at most N candidates"
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="only migrate this specific account -- use this for the required single-test-account run",
    )
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run, limit=args.limit, target_email=args.email))
