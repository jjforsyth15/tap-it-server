from app.models.user import User
from sqlalchemy.orm import Session
from sqlalchemy import func

def get_user_by_email(email: str, db: Session) -> User | None:
    normalized_email = normalize_email(email)
    return db.query(User).filter(func.lower(User.email) == normalized_email).first()



def normalize_email(email: str) -> str:
    return email.strip().lower()
