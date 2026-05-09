from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import uuid4
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.auth import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    
    errors = validate_register_data(user_data)
    if errors:
        raise HTTPException(status_code=400, detail={"detail": errors})
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email has already been registered")
    
    new_user = User(
        user_id=str(uuid4()),
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,        
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "email": new_user.email}


@router.post("/login")
def login(user_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.username).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user.email)})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
    }
    
def validate_register_data(user_data: UserRegister):
    errors = []
    
    if not user_data.email:
        errors.append("Missing email")
    if not user_data.password:
        errors.append("Missing password")
    if not user_data.first_name:
        errors.append("Missing first name")
    if not user_data.last_name:
        errors.append("Missing last name")

    return errors