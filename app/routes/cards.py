from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.card import Card

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