from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile import Profile, ProfileStatus
from app.models.card import Card, CardStatus
from app.models.profile_links import ProfileLink
from app.schemas.profile import ProfileCreate, ProfileCreateResponse, ProfileOrderUpdateRequest, ProfileResponse, ProfileUpdate, PublicProfileResponse
from app.core.dependencies import get_current_user
from uuid import UUID, uuid4
from datetime import datetime, timezone
from app.routes.validators import validate_profile_data, validate_profile_user
from app.core.rate_limiter import limiter


router = APIRouter(prefix="/profiles", tags=["profiles"])


 # Create profile - POST /profiles/create_profile - protected route
@router.post("/create_profile", response_model=ProfileCreateResponse)
@limiter.limit("5/hour")
def create_profile(
    request: Request,
    profile_data: ProfileCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    errors = validate_profile_data(profile_data)
    if errors:
        raise HTTPException(status_code=400, detail={"detail": errors})

    new_profile = Profile(
        profile_id=uuid4(),
        user_id=current_user.user_id,
        profile_name=profile_data.profile_name,
        bio=profile_data.bio,
        profile_status=profile_data.profile_status,
        profile_image_url=profile_data.profile_image_url
    )
    
    db.add(new_profile)
    try:
        db.commit()
        db.refresh(new_profile)
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Profile created successfully",
        "profile": new_profile
    }
    
    
# Get all profiles for current user - GET /profiles/me - protected route
@router.get("/me",response_model=list[ProfileResponse])
def get_my_profiles(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):    
    profiles = db.query(Profile).filter(Profile.user_id == current_user.user_id).order_by(Profile.display_order.asc(), Profile.created_at.asc()).all()
    
    for profile in profiles:
        add_link_and_card_counts(profile, db)

    return profiles


# Get public profile - GET /profiles/public/{profile_id} - public route
@router.get("/public/{profile_id}", response_model=PublicProfileResponse)
def get_public_profile(profile_id: UUID, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.profile_id == profile_id, Profile.profile_status == ProfileStatus.active).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


# Reorder profiles - PATCH /profiles/reorder - protected route
@router.patch("/reorder")
def reorder_profiles(updates: ProfileOrderUpdateRequest, db: Session = Depends(get_db), current_user= Depends(get_current_user)):
    profile_ids = [item.profile_id for item in updates.profiles]
    
    profiles = [validate_profile_user(profile_id, current_user, db) for profile_id in profile_ids]
    
    if len(profiles) != len(set(profile_ids)):
        raise HTTPException(status_code=400, detail="Profile reorder request contains duplicate profile IDs.")
    
    order_map = {item.profile_id: item.display_order for item in updates.profiles}
    
    for profile in profiles:
        profile.display_order = order_map[profile.profile_id]
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Profiles reordered successfully"}


# Get profile by ID - GET /profiles/{profile_id} - protected route
@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = validate_profile_user(profile_id, current_user, db)
    
    add_link_and_card_counts(profile, db)
    
    return profile


# Deactivate profile - PATCH /profiles/{profile_id}/deactivate - protected route
@router.patch("/{profile_id}/deactivate")
def deactivate_profile(profile_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = validate_profile_user(profile_id, current_user, db)
    
    profile.profile_status = ProfileStatus.inactive
    profile.updated_at = datetime.now(timezone.utc)
    
    db.query(Card).filter(Card.profile_id == profile_id, Card.card_status == CardStatus.active).update(
        {"card_status": "deactivated"}
    )
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Profile and associated cards deactivated successfully"}


# Activate profile - PATCH /profiles/{profile_id}/activate - protected route
@router.patch("/{profile_id}/activate")
def activate_profile(profile_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = validate_profile_user(profile_id, current_user, db)
    
    profile.profile_status = ProfileStatus.active
    profile.updated_at = datetime.now(timezone.utc)
    
    db.query(Card).filter(Card.profile_id == profile_id, Card.card_status == CardStatus.deactivated).update(
        {"card_status": "active"},
        synchronize_session=False,
    )
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Profile and associated cards activated successfully"}

# Update profile details - PATCH /profiles/{profile_id}/update_profile - protected route
@router.patch("/{profile_id}/update_profile")
@limiter.limit("20/hour")
def update_profile(request: Request, profile_id: UUID, profile_data: ProfileUpdate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):   
    profile = validate_profile_user(profile_id, current_user, db)

    update_data = profile_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    profile.updated_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return {
            "message": "Profile updated successfully",
            "profile": profile
            }
    
# Delete profile - DELETE /profiles/{profile_id} - protected route
@router.delete("/{profile_id}")
def delete_profile(profile_id: UUID, reassign_to_profile_id: UUID | None = None, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if reassign_to_profile_id == profile_id:
        raise HTTPException(status_code=400, detail="Cannot reassign cards to the same profile being deleted.")
    
    profile = validate_profile_user(profile_id, current_user, db)
    
    if reassign_to_profile_id:
        new_profile = validate_profile_user(reassign_to_profile_id, current_user, db)
        
        db.query(Card).filter(Card.profile_id == profile_id).update({Card.profile_id: reassign_to_profile_id})
        
        message = "Profile cards reassigned to: " + new_profile.profile_name
        
    else:
        db.query(Card).filter(Card.profile_id == profile_id).update({Card.profile_id: None})
        
        message = "Profile cards unassigned"
    
    db.delete(profile)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    
    return {"message": "Profile deleted successfully\n" + message}

# Add link and card counts to profile object
def add_link_and_card_counts(profile, db):
    profile.link_count = db.query(ProfileLink).filter(ProfileLink.profile_id == profile.profile_id).count()
    profile.card_count = db.query(Card).filter(Card.profile_id == profile.profile_id, Card.card_status == CardStatus.active).count()
    
    return profile