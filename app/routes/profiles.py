from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile import Profile
from app.models.card import Card
from app.schemas.profile import ProfileCreate, ProfileCreateResponse, ProfileResponse, ProfileUpdate
from app.core.dependencies import get_current_user
from uuid import UUID, uuid4
from datetime import datetime
from app.routes.validators import validate_profile_data, validate_profile_user


router = APIRouter(prefix="/profiles", tags=["profiles"])


 # Create profile - POST /profiles/create_profile
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
    
    
# Get all profiles for current user - GET /profiles/me 
@router.get("/me",response_model=list[ProfileResponse])
def get_my_profiles(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):    
    profiles = db.query(Profile).filter(Profile.user_id == current_user.user_id).all()
    
    return profiles


# Get profile by ID - GET /profiles/{profile_id}
@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = validate_profile_user(profile_id, current_user, db)
    
    return profile


# Deactivate profile - PATCH /profiles/{profile_id}/deactivate
@router.patch("/{profile_id}/deactivate")
def deactivate_profile(profile_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = validate_profile_user(profile_id, current_user, db)
    
    profile.is_active = False
    profile.updated_at = datetime.now()
    
    db.query(Card).filter(Card.profile_id == profile_id).update(
        {"card_status": "deactivated"}
    )
    
    db.commit()
    
    return {"message": "Profile and associated cards deactivated successfully"}


# Activate profile - PATCH /profiles/{profile_id}/activate
@router.patch("/{profile_id}/activate")
def activate_profile(profile_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = validate_profile_user(profile_id, current_user, db)
    
    profile.is_active = True
    profile.updated_at = datetime.now()
    
    db.query(Card).filter(Card.profile_id == profile_id).update(
        {"card_status": "active"}
    )
    
    db.commit()
    
    return {"message": "Profile and associated cards activated successfully"}
    

# Update profile website URL - PATCH /profiles/{profile_id}/update_website_url    
@router.patch("/{profile_id}/update_website_url")
def update_website_url(profile_id: UUID, website_url: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = validate_profile_user(profile_id, current_user, db)
    
    profile.website_url = website_url
    profile.updated_at = datetime.now()
    
    db.commit()
    db.refresh(profile)
    
    return {
            "message": "Profile website URL updated successfully",
            "profile_name": profile.profile_name,
            "new_website_url": profile.website_url
            }
 

# Update profile details - PATCH /profiles/{profile_id}/update_profile      ***update***
@router.patch("/{profile_id}/update_profile")
def update_profile(profile_id: UUID, profile_data: ProfileUpdate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):   
    profile = validate_profile_user(profile_id, current_user, db)

    update_data = profile_data.model_dump(exclude_unset=True)
    
    if "website_url" in update_data and update_data["website_url"] is not None:
        update_data["website_url"] = str(update_data["website_url"])
    
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    profile.updated_at = datetime.now()
    
    db.commit()
    db.refresh(profile)
    
    return {
            "message": "Profile updated successfully",
            "profile": profile
            }
    

@router.delete("/{profile_id}")
def delete_profile(profile_id: UUID, reassign_to_profile_id: UUID | None = None, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = validate_profile_user(profile_id, current_user, db)
    
    if reassign_to_profile_id:
        new_profile = validate_profile_user(reassign_to_profile_id, current_user, db)
        
        db.query(Card).filter(Card.profile_id == profile_id).update({Card.profile_id: reassign_to_profile_id})
        
        messsage = "Profile cards reassigned to: " + new_profile.profile_name
        
    else:
        db.query(Card).filter(Card.profile_id == profile_id).update({Card.profile_id: None})
        
        mwesssage = "Profile cards unassigned"
    
    db.delete(profile)
    db.commit()
    
    return {"message": "Profile deleted successfully\n" + messsage}