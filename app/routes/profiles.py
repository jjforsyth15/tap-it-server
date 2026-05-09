from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.core.dependencies import get_current_user
from uuid import uuid4
from datetime import datetime


router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.post("/create_profile", response_model=ProfileResponse)
def create_profile(
    profile_data: ProfileCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_profile = Profile(
        profile_id=str(uuid4()),
        user_id=current_user.user_id,
        profile_name=profile_data.profile_name,
        bio=profile_data.bio,
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return {"message": "Profile created successfully", "profile_name": new_profile.profile_name}


@router.get("/me",response_model=list[ProfileResponse])
def get_my_profiles(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profiles = db.query(Profile).filter(Profile.user_id == current_user.user_id).all()
    
    return profiles
