from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.card import Card, CardStatus
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.card import CardCreate
from uuid import uuid4
import string
import random


router = APIRouter(prefix="/cards", tags=["cards"])

@router.get("/{card_code}")
def get_card(card_code: str, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.card_code == card_code).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if card.card_status == "inactive":
        return RedirectResponse(url=f"/login?next=/cards/{card_code}")
    
    if card.card_status == "active":
        return RedirectResponse(url=f"/profile/{card.profile_id}")
    
    if card.card_status in ["deactivated", "lost", "disabled"]:
        raise HTTPException(status_code=403, detail="Card is not available")
    
    raise HTTPException(status_code=400, detail="Invalid card status")


@router.post("/create_card")
def create_card(card_data: CardCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    card_code = generate_card_code()
    
    new_card = Card(
        card_id=str(uuid4()),
        profile_id=current_user.user_id,
        card_name=card_data.card_name,
        card_code=card_code,
        pointing_url=f"/cards/{card_code}",
        card_status=CardStatus.inactive
    )
    
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    
    return {"message": "Card created successfully"}


def generate_card_code(length=8):
    return ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )