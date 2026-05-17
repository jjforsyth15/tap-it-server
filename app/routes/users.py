from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import uuid4
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.auth import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.routes.validators import validate_register_data
from app.schemas.user import UserUpdate, UserResponse

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
    db: Session = Depends(get_db)
):
    update_data = user_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
        
    db.commit()
    db.refresh(current_user)
    
    return current_user


# Delete current user account - DELETE /users/me
@router.delete("/me")
def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.is_active = False
    
    db.commit()
    
    return {"message": "User account deactivated successfully"}