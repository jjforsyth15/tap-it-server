from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.rate_limiter import limiter
from app.schemas.user import UserUpdate, UserResponse
from app.schemas.auth import (
    EmailChangeRequest,
    EmailChangeConfirmRequest,
    EmailChangeCancelRequest,
)
from app.services.email_change import (
    request_email_change,
    send_email_change_confirmation,
    send_email_change_notice,
    send_email_change_completed_notice,
    confirm_email_change,
    cancel_email_change,
)

router = APIRouter(prefix="/users", tags=["users"])


# Get current user info - GET /auth/me
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# Update current user info - PATCH /users/me
@router.patch("/me", response_model=UserUpdate)
def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = user_data.model_dump(exclude_unset=True)

    non_nullable_fields = ("first_name", "last_name")
    invalid_fields = [
        field
        for field in non_nullable_fields
        if field in update_data and update_data[field] is None
    ]

    if invalid_fields:
        raise HTTPException(
            status_code=422,
            detail=f"Fields cannot be null: {', '.join(invalid_fields)}",
        )

    for key, value in update_data.items():
        setattr(current_user, key, value)

    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise

    return current_user


# Request an email change - POST /users/me/email/change
@router.post("/me/email/change")
@limiter.limit("3/hour")
def change_email(
    request: Request,
    change_data: EmailChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change_token, confirm_token, cancel_token = request_email_change(
        current_user,
        str(change_data.new_email),
        change_data.current_password,
        change_data.google_credential,
        db,
    )

    send_email_change_confirmation(current_user, change_token.new_email, confirm_token)

    send_email_change_notice(current_user, change_token.new_email, cancel_token)

    return {
        "message": "Check the new email address for a link to confirm this change."
    }


# Confirm a pending email change - POST /users/me/email/confirm
@router.post("/me/email/confirm")
@limiter.limit("10/hour")
def confirm_email_change_route(
    request: Request,
    confirm_data: EmailChangeConfirmRequest,
    db: Session = Depends(get_db),
):
    user, old_email = confirm_email_change(confirm_data.token, db)

    send_email_change_completed_notice(old_email, user.email)

    return {"message": "Email changed successfully."}


# Cancel a pending email change - POST /users/me/email/cancel
@router.post("/me/email/cancel")
@limiter.limit("10/hour")
def cancel_email_change_route(
    request: Request,
    cancel_data: EmailChangeCancelRequest,
    db: Session = Depends(get_db),
):
    cancel_email_change(cancel_data.token, db)

    return {"message": "Pending email change cancelled."}


# Delete current user account - DELETE /users/me
@router.delete("/me")
def delete_current_user(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    current_user.is_active = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "User account deactivated successfully"}
