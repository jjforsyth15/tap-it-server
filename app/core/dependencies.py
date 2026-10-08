from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.auth import SECRET_KEY, ALGORITHM
from app.core.supabase_jwt import decode_supabase_token
from app.database import get_db
from app.models.user import User
from app.models.enums import UserType

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def resolve_supabase_user(payload: dict, db: Session) -> User | None:
    """Look up the local user mapped to a verified Supabase token's "sub" claim."""
    subject = payload.get("sub")
    if subject is None:
        return None

    try:
        auth_id = UUID(subject)
    except (TypeError, ValueError):
        return None

    return db.query(User).filter(User.supabase_auth_id == auth_id).first()


def token_issued_before_revocation(payload: dict, user: User) -> bool:
    """Supabase-equivalent of the local "tv" check -- see vault Decisions
    for the rationale and its known refresh-token limitation."""
    if user.token_version_updated_at is None:
        return False

    return payload["iat"] < user.token_version_updated_at.timestamp()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            user_id = UUID(subject)
        except (TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        # Tokens issued before this claim existed carry no "tv" and are treated
        # as version 0, matching every existing user's default -- so shipping
        # this check doesn't retroactively log everyone out.
        if payload.get("tv", 0) != user.token_version:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        # Not a local token -- try it as a Supabase-issued token instead.
        supabase_payload = decode_supabase_token(token)
        if supabase_payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = resolve_supabase_user(supabase_payload, db)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found: invalid token")

        if token_issued_before_revocation(supabase_payload, user):
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

        try:
            user_id = UUID(subject)
        except (TypeError, ValueError):
            return None

        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            return None

        if payload.get("tv", 0) != user.token_version:
            return None

    except JWTError:
        supabase_payload = decode_supabase_token(token)
        if supabase_payload is None:
            return None

        user = resolve_supabase_user(supabase_payload, db)
        if user is None:
            return None

        if token_issued_before_revocation(supabase_payload, user):
            return None

    if user.is_active is False:
        return None

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    return current_user
