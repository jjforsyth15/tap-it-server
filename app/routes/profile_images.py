from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.profile import Profile
from app.services.supabase_storage import upload_avatar
from app.routes.validators import validate_profile_user
from uuid import UUID

router = APIRouter(prefix="/profiles", tags=["Profile Images"])

# Need to complete to add images
@router.post("/{profile_id}/avatar")
async def upload_profile_avatar(
    profile_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user= Depends(get_current_user)
):
    profile = validate_profile_user(profile_id, current_user, db)
    
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, JPG, and WEBP are allowed.")
    
    file_bytes = await file.read()
    
    extension_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/jpg": "jpg",
        "image/webp": "webp",
    }
    
    extension = extension_map.get(file.content_type)
    
    if not extension:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    
    path = f"profiles/{profile_id}/avatar.{extension}"
    
    public_url = upload_avatar(
        file_bytes=file_bytes,
        path=path,
        content_type=file.content_type
    )
    
    profile.profile_image_url = public_url
    db.commit()
    db.refresh(profile)
    
    return {
        "message": "Profile avatar uploaded successfully",
        "profile": profile
    }