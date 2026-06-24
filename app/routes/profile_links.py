from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile_links import ProfileLink
from app.models.profile import Profile
from app.schemas import profile_link
from app.schemas.profile_link import ProfileLinkCreate, ProfileLinkReorderRequest, ProfileLinkResponse
from app.core.dependencies import get_current_user
from uuid import UUID, uuid4
from datetime import datetime
from app.routes.validators import validate_profile_user, validate_link_in_db


router = APIRouter(prefix="/profile_links", tags=["profile_links"])

# Create new profile link - POST /profile_links/{profile_id}/links
@router.post("/{profile_id}/links", response_model=ProfileLinkResponse)
def create_profile_link(
    profile_id: UUID,
    link_data: ProfileLinkCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = validate_profile_user(profile_id, current_user, db)

    new_link = ProfileLink(
        profile_id=profile_id,
        label=link_data.label,
        url=str(link_data.url)
    )
    
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    
    return new_link


# Get all links for a profile - GET /profile_links/{profile_id}/links
@router.get("/{profile_id}/links", response_model=list[ProfileLinkResponse])
def get_profile_links(
    profile_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    validate_profile_user(profile_id, current_user, db)
    
    links = db.query(ProfileLink).filter(ProfileLink.profile_id == profile_id).order_by(ProfileLink.display_order.asc(), ProfileLink.created_at.asc()).all()
    
    return links


# Update profile link - PATCH /profile_links/links/{link_id}
@router.patch("/links/{link_id}", response_model=ProfileLinkResponse)
def update_profile_link(
    link_id: UUID,
    link_data: ProfileLinkCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = validate_link_in_db(link_id, db)
    
    validate_profile_user(link.profile_id, current_user, db)
    
    update_data = link_data.model_dump(exclude_unset=True)
    
    if "url" in update_data and update_data["url"] is not None:
        update_data["url"] = str(update_data["url"])
    
    for key, value in update_data.items():
        setattr(link, key, value)

    db.commit()
    db.refresh(link)
    
    return link


# Delete profile link - DELETE /profile_links/links/{link_id}
@router.delete("/links/{link_id}")
def delete_profile_link(
    link_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = validate_link_in_db(link_id, db)
    
    validate_profile_user(link.profile_id, current_user, db)
    
    db.delete(link)
    db.commit()
    
    return {"message": "Profile link deleted successfully"}

# Get a specific profile link - GET /profile_links/links/{link_id}
@router.get("/links/{link_id}", response_model=ProfileLinkResponse)
def get_profile_link(
    link_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = validate_link_in_db(link_id, db)
    
    validate_profile_user(link.profile_id, current_user, db)
    
    return link

# Reorder profile links - PATCH /profile_links/reorder
@router.patch("/reorder")
def reorder_profile_links(payload: ProfileLinkReorderRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    for item in payload.links:
        link = validate_link_in_db(item.link_id, db)
        profile = validate_profile_user(link.profile_id, current_user, db)
        
        link.display_order = item.display_order
        
    db.commit()
    
    return {"message": "Profile links reordered successfully"}