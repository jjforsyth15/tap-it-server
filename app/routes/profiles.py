from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileCreateResponse, ProfileResponse
from app.core.dependencies import get_current_user
from uuid import uuid4
from datetime import datetime


router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.post("/create_profile", response_model=ProfileCreateResponse)
def create_profile(
    profile_data: ProfileCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    errors = validate_profile_data(profile_data)
    if errors:
        raise HTTPException(status_code=400, detail={"detail": errors})

    new_profile = Profile(
        profile_id=str(uuid4()),
        user_id=current_user.user_id,
        profile_name=profile_data.profile_name,
        bio=profile_data.bio,
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return {
        "message": "Profile created successfully",
        "profile": new_profile
    }


@router.get("/me",response_model=list[ProfileResponse])
def get_my_profiles(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profiles = db.query(Profile).filter(Profile.user_id == current_user.user_id).all()
    
    return profiles


def validate_profile_data(profile_data: ProfileCreate):
    errors = []
    
    if not profile_data.profile_name:
        errors.append("Missing profile name")
        
    if len(profile_data.profile_name) > 50:
        errors.append("Profile name must be 50 characters or less")
        
    if profile_data.bio and len(profile_data.bio) > 500:
        errors.append("Bio must be 500 characters or less")
    
    return errors