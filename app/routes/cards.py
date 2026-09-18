from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.card import Card, CardStatus
from app.core.dependencies import get_current_user
from app.models.enums import ProfileStatus
from app.models.user import User
from app.schemas.card import (
    CardAdjustmentResponse,
    CardCreate,
    CardResponse,
    CardCreateResponse,
    CardUpdate,
    PublicCardResponse,
    CardActivateRequest,
    CardReactivateRequest,
)
from uuid import UUID
from app.models.card_tap import CardTap
from uuid import uuid4
import string
import random
import os
from datetime import datetime
from app.routes.validators import (
    validate_profile_user,
    validate_card_data,
    validate_card_code_in_db,
    validate_card_id_in_db,
    validate_card_user,
)
from app.core.rate_limiter import limiter

frontend_url = os.getenv("FRONTEND_URL")

router = APIRouter(prefix="/cards", tags=["cards"])


# Get all cards for the current user - GET /cards - protected route
@router.get("", response_model=list[CardResponse])
def get_user_cards(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    cards = (
        db.query(Card)
        .filter(Card.user_id == current_user.user_id)
        .order_by(Card.created_at.desc())
        .all()
    )
    return cards


# Get public card info - GET /cards/{card_code}/public - public route
@router.get("/{card_code}/public", response_model=PublicCardResponse)
def get_public_card_info(card_code: str, db: Session = Depends(get_db)):
    card = validate_card_code_in_db(card_code, db)

    return PublicCardResponse(
        card_code=card.card_code,
        card_name=card.card_name,
        card_status=card.card_status,
        profile_id=card.profile_id if card.card_status == CardStatus.active else None,
    )


# Get card by card code - GET /cards/{card_code} - public route
@router.get("/{card_code}")
def get_card(card_code: str, db: Session = Depends(get_db)):
    card = validate_card_code_in_db(card_code, db)

    if card.card_status == "inactive":
        return RedirectResponse(
            url=f"{frontend_url}/login?next=/activate-card/{card_code}"
        )

    if card.card_status == "active":
        new_tap = CardTap(card_id=card.card_id)
        db.add(new_tap)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return RedirectResponse(url=f"{frontend_url}/public/{card.profile_id}")

    if card.card_status in ["deactivated", "lost", "disabled"]:
        raise HTTPException(status_code=403, detail="Card is not available")

    raise HTTPException(status_code=400, detail="Invalid card status")


# Create new card - POST /cards/create_card - protected route
@router.post("/create_card", response_model=CardCreateResponse)
@limiter.limit("10/hour")
def create_card(
    request: Request,
    card_data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    errors = validate_card_data(card_data)
    if errors:
        raise HTTPException(status_code=400, detail={"detail": errors})

    if card_data.profile_id:
        validate_profile_user(card_data.profile_id, current_user, db)

    card_code = generate_card_code(db)

    new_card = Card(
        card_id=str(uuid4()),
        profile_id=card_data.profile_id,
        user_id=current_user.user_id if card_data.profile_id else None,
        card_name=card_data.card_name,
        card_code=card_code,
        card_status=CardStatus.inactive,
    )

    db.add(new_card)
    try:
        db.commit()
        db.refresh(new_card)
    except Exception:
        db.rollback()
        raise

    return {"message": "Card created successfully", "card": new_card}


# Get all cards for a profile - GET /cards/profile/{profile_id} - protected route
@router.get("/profile/{profile_id}", response_model=list[CardResponse])
def get_cards_by_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_profile_user(profile_id, current_user, db)

    cards = db.query(Card).filter(Card.profile_id == profile_id).all()

    return cards


# Get active cards for a profile - GET /cards/profile/{profile_id}/active - protected route
@router.get("/profile/{profile_id}/active", response_model=list[CardResponse])
def get_active_cards_by_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_profile_user(profile_id, current_user, db)

    cards = (
        db.query(Card)
        .filter(Card.profile_id == profile_id, Card.card_status == "active")
        .all()
    )

    return cards


# Activate card - PATCH /cards/{card_code}/activate - protected route
@router.patch("/{card_code}/activate", response_model=CardAdjustmentResponse)
@limiter.limit("5/hour")
def activate_card(
    request: Request,
    card_code: str,
    request_data: CardActivateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = validate_card_code_in_db(card_code, db)

    if card.card_status == "active":
        raise HTTPException(status_code=400, detail="Card is already active")

    if card.card_status in ["lost", "deactivated", "disabled"]:
        raise HTTPException(
            status_code=403,
            detail="This card cannot be activated. Please contact support.",
        )

    if not card.profile_id:
        if not request_data.new_profile_id:
            raise HTTPException(
                status_code=400,
                detail="A profile must be provided to activate this card",
            )
        new_profile = validate_profile_user(request_data.new_profile_id, current_user, db)
        if new_profile.profile_status != ProfileStatus.active:
            raise HTTPException(
                status_code=403, detail="Cannot assign card to a non-active profile"
            )
        if card.user_id and card.user_id != current_user.user_id:
            raise HTTPException(
                status_code=403, detail="This card is already assigned to another user"
            )
        card.profile_id = request_data.new_profile_id
        card.user_id = current_user.user_id
    else:
        profile = validate_profile_user(card.profile_id, current_user, db)
        if profile.profile_status != ProfileStatus.active:
            raise HTTPException(
                status_code=403, detail="Cannot assign card to a non-active profile"
            )

    card.card_status = CardStatus.active
    card.activated_at = datetime.now()
    card.updated_at = datetime.now()

    try:
        db.commit()
        db.refresh(card)
    except Exception:
        db.rollback()
        raise

    return {"message": "Card activated successfully", "card": card}


# Deactivate card - PATCH /cards/{card_id}/deactivate - protected route
@router.patch("/{card_id}/deactivate", response_model=CardAdjustmentResponse)
def deactivate_card(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = validate_card_id_in_db(card_id, db)
    validate_card_user(card, current_user)

    if card.card_status == CardStatus.deactivated:
        raise HTTPException(status_code=400, detail="Card is already deactivated")

    if card.card_status != CardStatus.active:
        raise HTTPException(
            status_code=403, detail="Only an active card can be deactivated"
        )

    card.card_status = CardStatus.deactivated
    card.updated_at = datetime.now()

    try:
        db.commit()
        db.refresh(card)
    except Exception:
        db.rollback()
        raise

    return {"message": "Card deactivated successfully", "card": card}


# Report card lost - PATCH /cards/{card_id}/report-lost - protected route
@router.patch("/{card_id}/report-lost", response_model=CardAdjustmentResponse)
def report_card_lost(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = validate_card_id_in_db(card_id, db)
    validate_card_user(card, current_user)

    if card.card_status == CardStatus.lost:
        raise HTTPException(status_code=400, detail="Card is already reported lost")

    if card.card_status == CardStatus.disabled:
        raise HTTPException(
            status_code=403,
            detail="This card cannot be reported lost. Please contact support.",
        )

    card.card_status = CardStatus.lost
    card.updated_at = datetime.now()

    try:
        db.commit()
        db.refresh(card)
    except Exception:
        db.rollback()
        raise

    return {"message": "Card reported lost successfully", "card": card}


# Reactivate card - PATCH /cards/{card_id}/reactivate - protected route
@router.patch("/{card_id}/reactivate", response_model=CardAdjustmentResponse)
def reactivate_card(
    card_id: UUID,
    request_data: CardReactivateRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = validate_card_id_in_db(card_id, db)
    validate_card_user(card, current_user)

    if card.card_status == CardStatus.active:
        raise HTTPException(status_code=400, detail="Card is already active")

    if card.card_status != CardStatus.deactivated:
        raise HTTPException(
            status_code=403,
            detail="Only a deactivated card can be reactivated. Please contact support.",
        )

    new_profile_id = request_data.new_profile_id if request_data else None

    if not card.profile_id:
        if not new_profile_id:
            raise HTTPException(
                status_code=400,
                detail="A profile must be provided to reactivate this card",
            )
        new_profile = validate_profile_user(new_profile_id, current_user, db)
        if new_profile.profile_status != ProfileStatus.active:
            raise HTTPException(
                status_code=403, detail="Cannot assign card to a non-active profile"
            )
        card.profile_id = new_profile_id
    else:
        profile = validate_profile_user(card.profile_id, current_user, db)
        if profile.profile_status != ProfileStatus.active:
            raise HTTPException(
                status_code=403, detail="Cannot assign card to a non-active profile"
            )

    card.card_status = CardStatus.active
    card.updated_at = datetime.now()

    try:
        db.commit()
        db.refresh(card)
    except Exception:
        db.rollback()
        raise

    return {"message": "Card reactivated successfully", "card": card}


# swap card's profile - PATCH /cards/{card_id}/profile/{profile_id} - protected route
@router.patch("/{card_id}/profile/{profile_id}")
def swap_card_profile(
    card_id: str,
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = validate_card_id_in_db(card_id, db)

    validate_card_user(card, current_user)
    new_profile = validate_profile_user(profile_id, current_user, db)

    if new_profile.profile_status != ProfileStatus.active:
        raise HTTPException(
            status_code=403, detail="Cannot assign card to a non-active profile"
        )

    card.profile_id = profile_id
    card.updated_at = datetime.now()

    try:
        db.commit()
        db.refresh(card)
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Card profile updated successfully",
        "card_name": card.card_name,
        "new_profile_name": new_profile.profile_name,
        "profile_id": card.profile_id,
    }


# Update card - PATCH /cards/{card_id} - protected route
@router.patch("/{card_id}", response_model=CardAdjustmentResponse)
def update_card(
    card_id: UUID,
    card_data: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    card = validate_card_id_in_db(card_id, db)

    validate_card_user(card, current_user)

    update_data = card_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(card, field, value)

    try:
        db.commit()
        db.refresh(card)
    except Exception:
        db.rollback()
        raise

    return {"message": "Card updated successfully", "card": card}


# Get card activation info - GET /cards/{card_code}/activation_info - protected route
@router.get("/{card_code}/activation_info")
def get_card_activation_info(
    card_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = validate_card_code_in_db(card_code, db)

    if card.profile_id:
        if card.profile.user_id != current_user.user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to activate this card"
            )
    elif card.user_id and card.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to activate this card"
        )

    if card.card_status == "active":
        raise HTTPException(status_code=400, detail="Card is already active")

    if card.card_status in ["lost", "deactivated", "disabled"]:
        raise HTTPException(
            status_code=403,
            detail="This card cannot be activated. Please contact support.",
        )

    return {
        "card_code": card.card_code,
        "card_name": card.card_name,
        "card_status": card.card_status,
        "profile_id": card.profile_id,
        "can_activate": True,
    }


# helper function - generate unique card code
def generate_card_code(db: Session, length=8):
    characters = string.ascii_uppercase + string.digits

    while True:
        code = "".join(random.choices(characters, k=length))

        existing_card = db.query(Card).filter(Card.card_code == code).first()

        if not existing_card:
            return code
