import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

import resend
from resend.exceptions import ResendError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.email_verification_token import EmailVerificationToken

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

resend.api_key = RESEND_API_KEY

TOKEN_LIFETIME = timedelta(hours=24)


def create_verification_token(user: User, db: Session) -> EmailVerificationToken:
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.user_id,
        EmailVerificationToken.used_at.is_(None),
    ).delete()

    verification_token = EmailVerificationToken(
        user_id=user.user_id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + TOKEN_LIFETIME,
    )

    db.add(verification_token)
    db.commit()
    db.refresh(verification_token)

    return verification_token


def send_verification_email(user: User, token: str) -> None:
    verification_link = f"{FRONTEND_URL}/verify-email?token={token}"

    params: resend.Emails.SendParams = {
        "from": RESEND_FROM_EMAIL,
        "to": [user.email],
        "subject": "Verify your TapIt email",
        "html": (
            f"<p>Hi {user.first_name},</p>"
            "<p>Confirm your email to finish setting up your TapIt account:</p>"
            f'<p><a href="{verification_link}">Verify email</a></p>'
            "<p>This link expires in 24 hours.</p>"
        ),
    }

    try:
        resend.Emails.send(params)
    except ResendError as exc:
        logger.exception(
            "Failed to send verification email to user %s", user.user_id
        )
        raise HTTPException(
            status_code=500, detail="Failed to send verification email."
        ) from exc


def verify_email_token(token: str, db: Session) -> User:
    verification_token = (
        db.query(EmailVerificationToken)
        .filter(EmailVerificationToken.token == token)
        .first()
    )

    if verification_token is None:
        raise HTTPException(status_code=400, detail="Invalid verification token.")

    if verification_token.used_at is not None:
        raise HTTPException(
            status_code=400, detail="This verification link has already been used."
        )

    if verification_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400, detail="This verification link has expired."
        )

    user = verification_token.user
    user.is_verified = True
    verification_token.used_at = datetime.now(timezone.utc)

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.user_id,
        EmailVerificationToken.token_id != verification_token.token_id,
        EmailVerificationToken.used_at.is_(None),
    ).delete()

    db.commit()
    db.refresh(user)

    return user
