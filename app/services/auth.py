import os
from typing import Any
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.enums import UserType
from app.models.user import User
from uuid import uuid4
from app.core.auth import hash_password, verify_password, create_access_token
from app.schemas.auth import (
    UserLoginResponse,
    UserRegister,
    GoogleLinkResponse,
    GoogleUserRegister,
)
from app.services.user import get_user_by_email, normalize_email
import logging
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def verify_google_token(credential: str) -> dict[str, Any] | None:
    try:
        token_data = id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )

    except ValueError:
        return None

    if not token_data.get("email_verified"):
        return None

    return token_data


def get_user_google(subject: str, db: Session = Depends(get_db)) -> User | None:
    user = db.query(User).filter(User.google_subject == subject).first()

    if not user:
        return None

    return user


def create_new_user(user_data: UserRegister, db: Session) -> User:
    new_user = User(
        user_id=str(uuid4()),
        email=normalize_email(str(user_data.email)),
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        google_subject=None,
        is_verified=False,
        is_active=True,
        user_type=UserType.USER,
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email or Google account already exists.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error occurred while creating a new user.")
        raise HTTPException(
            status_code=500, detail="An error occurred while creating the user."
        ) from exc

    return new_user


def create_new_google_user(user_data: GoogleUserRegister, db: Session) -> User:
    new_user = User(
        user_id=str(uuid4()),
        email=normalize_email(str(user_data.email)),
        password_hash=None,  # No password for Google OAuth users
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        google_subject=user_data.google_subject,
        is_verified=True,  # Google OAuth users are considered verified
        is_active=True,
        user_type=UserType.USER,
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="An account with this email or Google account already exists."
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error occurred while creating a new Google user.")
        raise HTTPException(
            status_code=500, detail="An error occurred while creating the Google user."
        ) from exc

    return new_user


def login_user(
    user_data: OAuth2PasswordRequestForm, db: Session
) -> UserLoginResponse | None:
    email = normalize_email(user_data.username)
    user = get_user_by_email(email, db)

    if (
        not user
        or user.password_hash is None
        or user.is_active is False
        or not verify_password(user_data.password, user.password_hash)
    ):
        return None

    if not user.is_verified:
        raise HTTPException(
            status_code=403, detail="Please verify your email before logging in."
        )

    access_token = create_access_token(data={"sub": str(user.user_id)})

    response = UserLoginResponse(
        first_name=user.first_name,
        last_name=user.last_name,
        access_token=access_token,
        token_type="bearer",
    )

    return response


def link_google_account_service(
    token_data: dict[str, Any], current_user: User, db: Session
) -> GoogleLinkResponse:
    google_subject = token_data.get("sub")
    google_email = normalize_email(token_data.get("email"))

    if not google_subject or not google_email:
        return GoogleLinkResponse(
            success=False, message="Invalid Google token or email not verified."
        )

    if google_email != normalize_email(str(current_user.email)):
        return GoogleLinkResponse(
            success=False,
            message="Google account email does not match the current user's email.",
        )

    if current_user.google_subject == google_subject:
        return GoogleLinkResponse(
            success=False, message="Google account is already linked."
        )

    if current_user.google_subject is not None:
        return GoogleLinkResponse(
            success=False,
            message="Another Google account is already linked to this user.",
        )

    if current_user.is_active is False:
        return GoogleLinkResponse(
            success=False,
            message="User account is inactive. Cannot link Google account.",
        )

    linked_user = db.query(User).filter(User.google_subject == google_subject).first()

    if linked_user:
        return GoogleLinkResponse(
            success=False,
            message="This Google account is already linked to another user.",
        )

    current_user.google_subject = google_subject
    current_user.is_verified = True

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="This Google account is already linked."
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error occurred while linking Google account.")
        raise HTTPException(
            status_code=500, detail="An error occurred while linking the Google account."
        ) from exc

    return GoogleLinkResponse(
        success=True, message="Google account linked successfully."
    )


def login_google_user(user_data: User) -> UserLoginResponse:
    if not user_data.google_subject or not user_data.email:
        raise HTTPException(
            status_code=400, detail="Google account is not linked or email is missing."
        )

    if not user_data.is_active or not user_data.is_verified:
        raise HTTPException(
            status_code=403, detail="User account is inactive or not verified."
        )

    access_token = create_access_token(data={"sub": str(user_data.user_id)})

    response = UserLoginResponse(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        access_token=access_token,
        token_type="bearer",
    )

    return response
