from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile_links import ProfileLink
from app.models.profile import Profile
from app.schemas import profile_link
from app.schemas.profile_link import ProfileLinkCreate, ProfileLinkResponse
from app.core.dependencies import get_current_user
from uuid import UUID, uuid4
from datetime import datetime
from app.routes.validators import validate_profile_user


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


@router.get("/{profile_id}/links", response_model=list[ProfileLinkResponse])
def get_profile_links(
    profile_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = validate_profile_user(profile_id, current_user, db)
    
    links = db.query(ProfileLink).filter(ProfileLink.profile_id == profile_id).all()
    
    return links