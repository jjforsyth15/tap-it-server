from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
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
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user.email)})
    
    return {"access_token": access_token, "token_type": "bearer"}