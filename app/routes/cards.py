from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.card import Card, CardStatus
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.card import CardCreate, CardResponse, CardCreateResponse
from uuid import UUID
from app.models.profile import Profile
from uuid import uuid4
import string
import random
import os
from datetime import datetime

url = os.getenv("CURRENT_URL")


router = APIRouter(prefix="/cards", tags=["cards"])

@router.get("/{card_code}")
def get_card(card_code: str, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.card_code == card_code).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if card.card_status == "inactive":
        return RedirectResponse(url=f"{url}/login?next=/cards/{card_code}")
    
    if card.card_status == "active":
        return RedirectResponse(url=f"{url}/profile/{card.profile_id}")
    
    if card.card_status in ["deactivated", "lost", "disabled"]:
        raise HTTPException(status_code=403, detail="Card is not available")
    
    raise HTTPException(status_code=400, detail="Invalid card status")


@router.post("/create_card", response_model=CardCreateResponse)
def create_card(card_data: CardCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    errors = validate_card_data(card_data)
    if errors:
        raise HTTPException(status_code=400, detail={"detail": errors})
    
    profile = db.query(Profile).filter(
        Profile.profile_id == card_data.profile_id,
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if profile.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to create a card for this profile")

    card_code = generate_card_code(db)
    
    new_card = Card(
        card_id=str(uuid4()),
        profile_id=card_data.profile_id,
        card_name=card_data.card_name,
        card_code=card_code,
        pointing_url=f"{url}/cards/{card_code}",
        card_status="inactive"
    )
    
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    
    return {
        "message": "Card created successfully", 
        "card": new_card
        }


@router.get("/profile/{profile_id}", response_model=list[CardResponse])
def get_cards_by_profile(
    profile_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
    ):
        profile = db.query(Profile).filter(Profile.profile_id == profile_id).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        if profile.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="You do not have permission to view cards for this profile")
        
        return db.query(Card).filter(Card.profile_id == profile_id).all()
    
    
@router.patch("/{card_code}/activate")
def activate_card(card_code: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.card_code == card_code).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    profile = db.query(Profile).filter(Profile.profile_id == card.profile_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Associated profile not found")
    
    if profile.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to activate this card")
    
    if card.card_status in ["lost", "deactivated", "disabled"]:
        raise HTTPException(status_code=403, detail="This card cannot be activated. Please contact support.")
    
    card.card_status = CardStatus.active
    card.activated_at = datetime.now()
    card.updated_at = datetime.now()
    
    db.commit()
    db.refresh(card)
    
    return {
        "message": "Card activated successfully",
        "card_name:": card.card_name,
        "card_status": card.card_status,
        }


def generate_card_code(db: Session, length=8):
    characters = string.ascii_uppercase + string.digits
    
    while True:
        code = ''.join(random.choices(characters, k=length))
        
        existing_card = db.query(Card).filter(Card.card_code == code).first()
        
        if not existing_card:
            return code
    
def validate_card_data(card_data: CardCreate):
    errors = []
    
    if not card_data.profile_id:
        errors.append("Missing profile id")
        
    if not card_data.card_name:
        errors.append("Missing card name")
        
    if len(card_data.card_name) > 50:
        errors.append("Card name must be 50 characters or less")
    
    return errors