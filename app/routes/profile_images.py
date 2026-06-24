from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.profile import Profile
from app.services.supabase_storage import upload_avatar

router = APIRouter(prefix="/profiles", tags=["Profile Images"])

# Need to complete to add images