from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.validators import validate_profile_user

router = APIRouter(prefix="/beta", tags=["beta"])

