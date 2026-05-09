from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.card import Card, CardStatus
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.card import CardCreate, CardResponse, CardCreateResponse, CardStatusUpdate
from uuid import UUID
from app.models.profile import Profile
from app.models.card_tap import CardTap
from uuid import uuid4
import string
import random
import os
from datetime import datetime


router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/{card_id}/tap_count")
def get_card_tap_count(card_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.card_id == card_id).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card = db.query(Card).join(Profile).filter(Card.card_id == card_id, Profile.user_id == current_user.user_id).first()
    
    if not card:
        raise HTTPException(status_code=403, detail="You do not have permission to view analytics for this card")
    
    tap_count = db.query(func.count(CardTap.tap_id)).filter(CardTap.card_id == card_id).scalar()
    
    return {
        "card_name": card.card_name, 
        "tap_count": tap_count
        }