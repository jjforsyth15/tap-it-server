import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import resend
from resend.exceptions import ResendError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

resend.api_key = RESEND_API_KEY

TOKEN_LIFETIME = timedelta(hours=1)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_reset_token(user: User, db: Session) -> str:
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.used_at.is_(None),
    ).delete()

    token = secrets.token_urlsafe(32)

    reset_token = PasswordResetToken(
        user_id=user.user_id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + TOKEN_LIFETIME,
    )

    db.add(reset_token)
    db.commit()

    return token


def send_password_reset_email(user: User, token: str) -> None:
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    params: resend.Emails.SendParams = {
        "from": RESEND_FROM_EMAIL,
        "to": [user.email],
        "subject": "Reset your TapIt password",
        "html": (
            f"<p>Hi {user.first_name},</p>"
            "<p>We received a request to reset your TapIt password:</p>"
            f'<p><a href="{reset_link}">Reset password</a></p>'
            "<p>This link expires in 1 hour. If you didn't request this, you can ignore this email.</p>"
        ),
    }

    try:
        resend.Emails.send(params)
    except ResendError as exc:
        logger.exception(
            "Failed to send password reset email to user %s", user.user_id
        )
        raise HTTPException(
            status_code=500, detail="Failed to send password reset email."
        ) from exc


def reset_password(token: str, new_password: str, db: Session) -> User:
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == hash_token(token))
        .with_for_update()
        .first()
    )

    if reset_token is None:
        raise HTTPException(status_code=400, detail="Invalid reset token.")

    if reset_token.used_at is not None:
        raise HTTPException(
            status_code=400, detail="This reset link has already been used."
        )

    if reset_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This reset link has expired.")

    user = reset_token.user
    user.password_hash = hash_password(new_password)
    user.token_version += 1
    reset_token.used_at = datetime.now(timezone.utc)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.token_id != reset_token.token_id,
        PasswordResetToken.used_at.is_(None),
    ).delete()

    db.commit()
    db.refresh(user)

    return user
