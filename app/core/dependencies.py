from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.auth import SECRET_KEY, ALGORITHM
from app.database import get_db
from app.models.user import User
from app.models.enums import UserType

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        user_id = UUID(subject)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    # Tokens issued before this claim existed carry no "tv" and are treated as
    # version 0, matching every existing user's default -- so shipping this
    # check doesn't retroactively log everyone out.
    if payload.get("tv", 0) != user.token_version:
        raise HTTPException(status_code=401, detail="Invalid token")

    if user.is_active is False:
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)
) -> User | None:
    if token is None:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")

        if subject is None:
            return None

    except JWTError:
        return None

    try:
        user_id = UUID(subject)
    except (TypeError, ValueError):
        return None

    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None or user.is_active is False:
        return None

    if payload.get("tv", 0) != user.token_version:
        return None

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    return current_user
