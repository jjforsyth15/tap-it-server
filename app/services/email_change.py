import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import resend
from resend.exceptions import ResendError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import verify_password
from app.models.user import User
from app.models.email_change_token import EmailChangeToken
from app.services.auth import verify_google_token
from app.services.password_reset import hash_token
from app.services.user import get_user_by_email, normalize_email

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

resend.api_key = RESEND_API_KEY

TOKEN_LIFETIME = timedelta(hours=1)


def verify_step_up_credential(
    current_user: User, current_password: str | None, google_credential: str | None
) -> None:
    if current_password is not None:
        if current_user.password_hash is None:
            raise HTTPException(
                status_code=400,
                detail="This account does not have a password. Provide google_credential instead.",
            )

        if not verify_password(current_password, current_user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect password.")

        return

    token_data: dict[str, Any] | None = verify_google_token(google_credential)

    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid Google credential.")

    if (
        not current_user.google_subject
        or token_data.get("sub") != current_user.google_subject
    ):
        raise HTTPException(
            status_code=401, detail="Google credential does not match this account."
        )


def request_email_change(
    current_user: User,
    new_email: str,
    current_password: str | None,
    google_credential: str | None,
    db: Session,
) -> tuple[EmailChangeToken, str, str]:
    normalized_new_email = normalize_email(new_email)

    if normalized_new_email == normalize_email(str(current_user.email)):
        raise HTTPException(
            status_code=400, detail="New email must be different from the current email."
        )

    existing_user = get_user_by_email(normalized_new_email, db)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email has already been registered")

    verify_step_up_credential(current_user, current_password, google_credential)

    db.query(EmailChangeToken).filter(
        EmailChangeToken.user_id == current_user.user_id,
        EmailChangeToken.used_at.is_(None),
        EmailChangeToken.cancelled_at.is_(None),
    ).delete()

    confirm_token = secrets.token_urlsafe(32)
    cancel_token = secrets.token_urlsafe(32)

    change_token = EmailChangeToken(
        user_id=current_user.user_id,
        new_email=normalized_new_email,
        confirm_token_hash=hash_token(confirm_token),
        cancel_token_hash=hash_token(cancel_token),
        expires_at=datetime.now(timezone.utc) + TOKEN_LIFETIME,
    )

    db.add(change_token)
    db.commit()
    db.refresh(change_token)

    return change_token, confirm_token, cancel_token


def send_email_change_confirmation(user: User, new_email: str, confirm_token: str) -> None:
    confirm_link = f"{FRONTEND_URL}/confirm-email-change?token={confirm_token}"

    params: resend.Emails.SendParams = {
        "from": RESEND_FROM_EMAIL,
        "to": [new_email],
        "subject": "Confirm your new TapIt email address",
        "html": (
            f"<p>Hi {user.first_name},</p>"
            "<p>Confirm this address to finish changing the email on your TapIt account:</p>"
            f'<p><a href="{confirm_link}">Confirm new email</a></p>'
            "<p>This link expires in 1 hour. If you didn't request this, you can ignore this email.</p>"
        ),
    }

    try:
        resend.Emails.send(params)
    except ResendError as exc:
        logger.exception(
            "Failed to send email-change confirmation to user %s", user.user_id
        )
        raise HTTPException(
            status_code=500, detail="Failed to send confirmation email."
        ) from exc


def send_email_change_notice(user: User, new_email: str, cancel_token: str) -> None:
    cancel_link = f"{FRONTEND_URL}/cancel-email-change?token={cancel_token}"

    params: resend.Emails.SendParams = {
        "from": RESEND_FROM_EMAIL,
        "to": [user.email],
        "subject": "Email change requested on your TapIt account",
        "html": (
            f"<p>Hi {user.first_name},</p>"
            f"<p>Someone requested to change the email on your TapIt account to {new_email}.</p>"
            "<p>If this was you, no action is needed until you confirm the new address.</p>"
            f'<p>If this wasn\'t you, <a href="{cancel_link}">cancel this request</a> '
            "and consider resetting your password.</p>"
        ),
    }

    try:
        resend.Emails.send(params)
    except ResendError:
        logger.exception(
            "Failed to send email-change notice to user %s", user.user_id
        )


def send_email_change_completed_notice(old_email: str, new_email: str) -> None:
    params: resend.Emails.SendParams = {
        "from": RESEND_FROM_EMAIL,
        "to": [old_email],
        "subject": "Your TapIt account email was changed",
        "html": (
            "<p>The email on your TapIt account was just changed "
            f"to {new_email}.</p>"
            "<p>If you didn't make this change, contact support immediately.</p>"
        ),
    }

    try:
        resend.Emails.send(params)
    except ResendError:
        logger.exception("Failed to send email-change completion notice to %s", old_email)


def confirm_email_change(token: str, db: Session) -> tuple[User, str]:
    change_token = (
        db.query(EmailChangeToken)
        .filter(EmailChangeToken.confirm_token_hash == hash_token(token))
        .with_for_update()
        .first()
    )

    if change_token is None:
        raise HTTPException(status_code=400, detail="Invalid confirmation token.")

    if change_token.cancelled_at is not None:
        raise HTTPException(status_code=400, detail="This email change was cancelled.")

    if change_token.used_at is not None:
        raise HTTPException(
            status_code=400, detail="This confirmation link has already been used."
        )

    if change_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400, detail="This confirmation link has expired."
        )

    existing_user = get_user_by_email(change_token.new_email, db)
    if existing_user and existing_user.user_id != change_token.user_id:
        raise HTTPException(status_code=409, detail="Email has already been registered")

    user = change_token.user
    old_email = user.email
    user.email = change_token.new_email
    change_token.used_at = datetime.now(timezone.utc)

    db.query(EmailChangeToken).filter(
        EmailChangeToken.user_id == user.user_id,
        EmailChangeToken.token_id != change_token.token_id,
        EmailChangeToken.used_at.is_(None),
        EmailChangeToken.cancelled_at.is_(None),
    ).delete()

    db.commit()
    db.refresh(user)

    return user, old_email


def cancel_email_change(token: str, db: Session) -> None:
    change_token = (
        db.query(EmailChangeToken)
        .filter(EmailChangeToken.cancel_token_hash == hash_token(token))
        .with_for_update()
        .first()
    )

    if change_token is None:
        raise HTTPException(status_code=400, detail="Invalid cancellation token.")

    if change_token.used_at is not None:
        raise HTTPException(
            status_code=400, detail="This email change has already been confirmed."
        )

    if change_token.cancelled_at is not None:
        raise HTTPException(
            status_code=400, detail="This email change has already been cancelled."
        )

    change_token.cancelled_at = datetime.now(timezone.utc)

    db.commit()
