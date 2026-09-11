from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User, UserType
from app.schemas.auth import UserRegister
from app.routes.validators import validate_register_data
from app.core.rate_limiter import limiter
from app.services.auth import (
    create_new_google_user,
    login_user,
    verify_google_token,
    get_user_google,
    create_new_user,
    login_google_user,
    link_google_account_service,
)
from app.schemas.auth import GoogleLoginRequest, UserLoginResponse, GoogleUserRegister
from app.services.user import get_user_by_email, normalize_email


router = APIRouter(prefix="/auth", tags=["authentication"])


# User registration - POST /auth/register
@router.post("/register")
@limiter.limit("5/hour")
def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):

    errors = validate_register_data(user_data)
    if errors:
        raise HTTPException(status_code=400, detail={"detail": errors})

    existing_user = get_user_by_email(str(user_data.email), db)

    if existing_user:
        raise HTTPException(status_code=400, detail="Email has already been registered")

    new_user = create_new_user(user_data, db)

    return {"message": "User registered successfully", "email": new_user.email}


# User login - POST /auth/login
@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    user_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> UserLoginResponse:
    user = login_user(user_data, db)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return user


@router.post("/google")
@limiter.limit("5/minute")
def google_oauth(
    request: Request, google_data: GoogleLoginRequest, db: Session = Depends(get_db)
) -> UserLoginResponse:
    token_data = verify_google_token(google_data.credential)
    if token_data is None:
        raise HTTPException(
            status_code=401, detail="Invalid Google token or email not verified."
        )

    if not token_data.get("sub") or not token_data.get("email"):
        raise HTTPException(
            status_code=401, detail="Invalid Google token or email not verified."
        )

    subject = token_data.get("sub")
    email = normalize_email(str(token_data["email"]))

    google_user = get_user_google(subject, db)

    if google_user:
        return login_google_user(google_user)

    existing_user = get_user_by_email(email, db)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists. Please log in using your email and password.",
        )

    email_name = email.split("@", maxsplit=1)[0]
    first_name = (
        token_data.get("given_name") or token_data.get("name") or email_name
    ).strip()
    last_name = (token_data.get("family_name") or "").strip()

    new_user_data = GoogleUserRegister(
        email=email,
        first_name=first_name,
        last_name=last_name,
        google_subject=subject,
        user_type=UserType.USER,
    )

    new_user = create_new_google_user(new_user_data, db)

    return login_google_user(new_user)


@router.post("/google/link")
@limiter.limit("5/minute")
def link_google_account(
    request: Request,
    google_data: GoogleLoginRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token_data = verify_google_token(google_data.credential)
    if token_data is None:
        raise HTTPException(
            status_code=401, detail="Invalid Google token or email not verified."
        )

    if not token_data.get("sub") or not token_data.get("email"):
        raise HTTPException(
            status_code=401, detail="Invalid Google token or email not verified."
        )

    if current_user.is_active is False:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive. Cannot link Google account.",
        )

    response = link_google_account_service(token_data, current_user, db)

    if response.success is False:
        raise HTTPException(status_code=400, detail=response.message)

    return response
