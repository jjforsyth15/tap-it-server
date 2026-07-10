from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.card import Card, CardStatus
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.card import CardAdjustmentResponse, CardCreate, CardResponse, CardCreateResponse, CardStatusUpdate, CardUpdate, PublicCardResponse, CardActivateRequest
from uuid import UUID
from app.models.profile import Profile
from app.models.card_tap import CardTap
from uuid import uuid4
import string
import random
import os
from datetime import datetime
from app.routes.validators import validate_profile_user, validate_card_data, validate_card_code_in_db, validate_card_id_in_db, validate_card_status, validate_card_profile_user

url = os.getenv("CURRENT_URL")
frontend_url = os.getenv("FRONTEND_URL")

router = APIRouter(prefix="/cards", tags=["cards"])

# Get all cards for the current user - GET /cards
@router.get("", response_model=list[CardResponse])
def get_user_cards(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    cards = db.query(Card).filter(Card.user_id == current_user.user_id).order_by(Card.created_at.desc()).all()
    return cards

# Get public card info - GET /cards/{card_code}/public
@router.get("/{card_code}/public", response_model=PublicCardResponse)
def get_public_card_info(card_code: str, db: Session = Depends(get_db)):
    card = validate_card_code_in_db(card_code, db)

    return card

# Get card by card code - GET /cards/{card_code}
@router.get("/{card_code}")
def get_card(card_code: str, db: Session = Depends(get_db)):
    card = validate_card_code_in_db(card_code, db)

    if card.card_status == "inactive":
        return RedirectResponse(url=f"{frontend_url}/login?next=/activate-card/{card_code}")
    
    if card.card_status == "active":
        new_tap = CardTap(card_id=card.card_id)
        db.add(new_tap)
        db.commit()

        return RedirectResponse(url=f"{frontend_url}/public/{card.profile_id}")
    
    if card.card_status in ["deactivated", "lost", "disabled"]:
        raise HTTPException(status_code=403, detail="Card is not available")
    
    raise HTTPException(status_code=400, detail="Invalid card status")


# Create new card - POST /cards/create_card
@router.post("/create_card", response_model=CardCreateResponse)
def create_card(card_data: CardCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    errors = validate_card_data(card_data)
    if errors:
        raise HTTPException(status_code=400, detail={"detail": errors})
    
    if card_data.profile_id:
        validate_profile_user(card_data.profile_id, current_user, db)

    card_code = generate_card_code(db)
    
    new_card = Card(
        card_id=str(uuid4()),
        profile_id=card_data.profile_id,
        card_name=card_data.card_name,
        card_code=card_code,
        pointing_url=f"{url}/cards/{card_code}",
        card_status=CardStatus.inactive
    )
    
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    
    return {
        "message": "Card created successfully", 
        "card": new_card
        }


# Get all cards for a profile - GET /cards/profile/{profile_id}
@router.get("/profile/{profile_id}", response_model=list[CardResponse])
def get_cards_by_profile(
    profile_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
    ):
        profile = validate_profile_user(profile_id, current_user, db)
        
        cards = db.query(Card).filter(Card.profile_id == profile_id).all()
        
        return cards
    
@router.get("/profile/{profile_id}/active", response_model=list[CardResponse])
def get_active_cards_by_profile(
    profile_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    profile = validate_profile_user(profile_id, current_user, db)
    
    cards = db.query(Card).filter(Card.profile_id == profile_id, Card.card_status == "active").all()
    
    return cards
    

# Activate card - PATCH /cards/{card_code}/activate    
@router.patch("/{card_code}/activate", response_model=CardAdjustmentResponse)
def activate_card(request_data: CardActivateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = validate_card_code_in_db(request_data.card_code, db)
    
    if card.card_status == "active":
        raise HTTPException(status_code=400, detail="Card is already active")
    
    if card.card_status in ["lost", "deactivated", "disabled"]:
        raise HTTPException(status_code=403, detail="This card cannot be activated. Please contact support.")
    
    if not card.profile_id:
        profile = validate_profile_user(request_data.new_profile_id, current_user, db)
        card.profile_id = request_data.new_profile_id
    else:
        validate_profile_user(card.profile_id, current_user, db)
    
    card.card_status = CardStatus.active
    card.activated_at = datetime.now()
    card.updated_at = datetime.now()
    
    db.commit()
    db.refresh(card)
    
    return {
        "message": "Card activated successfully",
        "card": card
        }
    

# swap card's profile - PATCH /cards/{card_id}/profile/{profile_id}
@router.patch("/{card_id}/profile/{profile_id}")
def swap_card_profile(card_id: str, profile_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = validate_card_id_in_db(card_id, db)
    
    new_profile = db.query(Profile).filter(Profile.profile_id == profile_id).first()
    
    if not new_profile:
        raise HTTPException(status_code=404, detail="New profile not found")
    
    if profile_id != current_user.user_id or new_profile.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to assign this card to the new profile")
    
    if new_profile.is_active == False:
        raise HTTPException(status_code=403, detail="Cannot assign card to an inactive profile")
    
    card.profile_id = profile_id
    card.updated_at = datetime.now()
    
    db.commit()
    db.refresh(card)
    
    return {
        "message": "Card profile updated successfully",
        "card_name": card.card_name,
        "new_profile_name": new_profile.profile_name,
        "profile_id": card.profile_id
        }


# Update card - PATCH /cards/{card_id}
@router.patch("/{card_id}", response_model=CardAdjustmentResponse)
def update_card(card_id: UUID, card_data: CardUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    card = validate_card_id_in_db(card_id, db)
    
    validate_profile_user(card.profile_id, current_user, db)
    
    update_data = card_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(card, field, value)
        
    # if card_data.card_status == CardStatus.deactivated or card_data.card_status == CardStatus.lost:
    #     card.profile_id = None
    
    db.commit()
    db.refresh(card)
    
    return {
        "message": "Card updated successfully",
        "card": card
        }
    

# Get card activation info - GET /cards/{card_code}/activation_info
@router.get("/{card_code}/activation_info")
def get_card_activation_info(card_code: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = validate_card_code_in_db(card_code, db)
    
    if card.profile_id:
        if card.profile.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to activate this card")
    
    if card.card_status == "active":
        raise HTTPException(status_code=400, detail="Card is already active")
    
    if card.card_status in ["lost", "deactivated", "disabled"]:
        raise HTTPException(status_code=403, detail="This card cannot be activated. Please contact support.")    
    
    
    return {
        "card_code": card.card_code,
        "card_name": card.card_name,
        "card_status": card.card_status,
        "profile_id": card.profile_id,
        "can_activate": True
    }
    
# Assign card to profile - PATCH /cards/{card_id}/assign_profile
@router.patch("/{card_id}/assign_profile", response_model=CardCreateResponse)
def assign_card_to_profile(card_id: UUID, profile_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = validate_card_id_in_db(card_id, db)
    profile = validate_profile_user(profile_id, current_user, db)
    
    card.profile_id = profile_id
    
    card.updated_at = datetime.now()
    db.commit()
    db.refresh(card)
    
    return {
        "message": f"Card assigned to profile {profile.profile_name} successfully",
        "card": card
    }


# Deactivate card - DELETE /cards/{card_id}
@router.patch("/{card_id}/deactivate")
def deactivate_card(card_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = validate_card_id_in_db(card_id, db)
    profile = validate_profile_user(card.profile_id, current_user, db)
    
    card.card_status = CardStatus.deactivated
    card.updated_at = datetime.now()
    
    db.commit()
    db.refresh(card)
        
    return {"message": f"Card {card.card_name} deactivated successfully"}


# helper function - generate unique card code
def generate_card_code(db: Session, length=8):
    characters = string.ascii_uppercase + string.digits
    
    while True:
        code = ''.join(random.choices(characters, k=length))
        
        existing_card = db.query(Card).filter(Card.card_code == code).first()
        
        if not existing_card:
            return code
    
