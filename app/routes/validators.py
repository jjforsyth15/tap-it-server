from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.card import Card
from app.models.profile import Profile
from uuid import UUID
from app.models.profile_links import ProfileLink
from app.schemas.auth import UserRegister
from app.schemas.card import CardCreate, CardStatusUpdate
from app.schemas.profile import ProfileCreate


# validate user authorization for profile access
def validate_profile_user(profile_id: UUID, current_user: User, db: Session):
    profile = db.query(Profile).filter(Profile.profile_id == profile_id, Profile.user_id == current_user.user_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


# validate profile data for create/update
def validate_profile_data(profile_data: ProfileCreate):
    errors = []
    
    if not profile_data.profile_name:
        errors.append("Missing profile name")
        
    if len(profile_data.profile_name) > 50:
        errors.append("Profile name must be 50 characters or less")
        
    if profile_data.bio and len(profile_data.bio) > 500:
        errors.append("Bio must be 500 characters or less")
    
    return errors


# validate card data for create
def validate_card_data(card_data: CardCreate):
    errors = []
        
    if not card_data.card_name:
        errors.append("Missing card name")
        
    if len(card_data.card_name) > 50:
        errors.append("Card name must be 50 characters or less")
        
    if len(card_data.card_name) < 1:
        errors.append("Card name must be at least 1 character")
    
    return errors


# validate registration data
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


# validate profile link exists in database
def validate_link_in_db(link_id: UUID, db: Session):
    link = db.query(ProfileLink).filter(ProfileLink.link_id == link_id).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Profile link not found")
    
    return link


# validate card exists in database
def validate_card_code_in_db(card_code: str, db: Session):
    card = db.query(Card).filter(Card.card_code == card_code).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return card

def validate_card_id_in_db(card_id: UUID, db: Session):
    card = db.query(Card).filter(Card.card_id == card_id).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return card


def validate_card_status(status_data: CardStatusUpdate):
    valid_statuses = [
        "inactive", 
        "active", 
        "deactivated",
        "lost",
        "disabled"
    ]
    
    if status_data.card_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid card status")
    
    return True
    

# validate card belongs to profile and user
def validate_card_profile_user(card_id: UUID, profile_id: UUID, current_user: User, db: Session):
    valid_card = validate_card_id_in_db(card_id, db)
    profile = validate_profile_user(profile_id, current_user, db)
    
    if valid_card.profile_id != profile.profile_id:
        raise HTTPException(status_code=403, detail="Card does not belong to the specified profile")
    
    return valid_card, profile