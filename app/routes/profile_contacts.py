from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile import Profile
from app.models.profile_contact import ProfileContact
from app.schemas.profile_contact import (
    ProfileContactCreate,
    ProfileContactReorderRequest,
    ProfileContactResponse,
    ProfileContactUpdate,
)
from app.core.dependencies import get_current_user
from uuid import UUID
from app.routes.validators import validate_profile_user, validate_contact_in_db
from app.services.profile_contacts import build_new_contact, apply_contact_update
from app.core.rate_limiter import limiter


router = APIRouter(prefix="/profile_contacts", tags=["profile_contacts"])


# Create new profile contact - POST /profile_contacts/{profile_id}/contacts - protected route
@router.post("/{profile_id}/contacts", response_model=ProfileContactResponse)
@limiter.limit("10/hour")
def create_profile_contact(
    request: Request,
    profile_id: UUID,
    contact_data: ProfileContactCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_profile_user(profile_id, current_user, db)

    contact = build_new_contact(profile_id, contact_data, db)

    try:
        db.commit()
        db.refresh(contact)
    except Exception:
        db.rollback()
        raise

    return contact


# Get all contacts for a profile - GET /profile_contacts/{profile_id}/contacts - protected route
@router.get("/{profile_id}/contacts", response_model=list[ProfileContactResponse])
def get_profile_contacts(
    profile_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_profile_user(profile_id, current_user, db)

    contacts = (
        db.query(ProfileContact)
        .filter(ProfileContact.profile_id == profile_id)
        .order_by(ProfileContact.display_order.asc(), ProfileContact.created_at.asc())
        .all()
    )

    return contacts


# Update profile contact - PATCH /profile_contacts/contacts/{contact_id} - protected route
@router.patch("/contacts/{contact_id}", response_model=ProfileContactResponse)
@limiter.limit("20/hour")
def update_profile_contact(
    request: Request,
    contact_id: UUID,
    contact_data: ProfileContactUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = validate_contact_in_db(contact_id, db)
    validate_profile_user(contact.profile_id, current_user, db)

    update_data = contact_data.model_dump(exclude_unset=True)

    apply_contact_update(contact, update_data, db)

    try:
        db.commit()
        db.refresh(contact)
    except Exception:
        db.rollback()
        raise

    return contact


# Delete profile contact - DELETE /profile_contacts/contacts/{contact_id} - protected route
@router.delete("/contacts/{contact_id}")
def delete_profile_contact(
    contact_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    contact = validate_contact_in_db(contact_id, db)
    validate_profile_user(contact.profile_id, current_user, db)

    db.delete(contact)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Profile contact deleted successfully"}


# Get a specific profile contact - GET /profile_contacts/contacts/{contact_id} - protected route
@router.get("/contacts/{contact_id}", response_model=ProfileContactResponse)
def get_profile_contact(
    contact_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    contact = validate_contact_in_db(contact_id, db)
    validate_profile_user(contact.profile_id, current_user, db)

    return contact


# Reorder profile contacts - PATCH /profile_contacts/reorder - protected route
@router.patch("/reorder")
@limiter.limit("20/hour")
def reorder_profile_contacts(
    request: Request,
    payload: ProfileContactReorderRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact_ids = {item.contact_id for item in payload.contacts}

    contacts = (
        db.query(ProfileContact)
        .filter(ProfileContact.contact_id.in_(contact_ids))
        .all()
    )
    contacts_by_id = {contact.contact_id: contact for contact in contacts}

    if len(contacts_by_id) != len(contact_ids):
        raise HTTPException(status_code=404, detail="Profile contact not found")

    profile_ids = {contact.profile_id for contact in contacts}
    owned_profile_ids = {
        profile_id
        for (profile_id,) in db.query(Profile.profile_id).filter(
            Profile.profile_id.in_(profile_ids),
            Profile.user_id == current_user.user_id,
        )
    }

    if profile_ids - owned_profile_ids:
        raise HTTPException(status_code=404, detail="Profile contact not found")

    for item in payload.contacts:
        contacts_by_id[item.contact_id].display_order = item.display_order

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Profile contacts reordered successfully"}
