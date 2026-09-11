from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.user import UserUpdate, UserResponse
from app.services.user import get_user_by_email, normalize_email

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

    non_nullable_fields = ("email", "first_name", "last_name")
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

    if "email" in update_data and update_data["email"] is not None:
        normalized_email = normalize_email(str(update_data["email"]))
        existing_user = get_user_by_email(normalized_email, db)

        if existing_user and existing_user.user_id != current_user.user_id:
            raise HTTPException(status_code=409, detail="Email has already been registered")

        update_data["email"] = normalized_email

    for key, value in update_data.items():
        setattr(current_user, key, value)

    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise

    return current_user


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
