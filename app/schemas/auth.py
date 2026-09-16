import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.models.user import UserType


def validate_password_complexity(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must contain at least one special character")
    return password


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    user_type: UserType = UserType.USER

    @field_validator("password")
    @classmethod
    def check_password_complexity(cls, value: str) -> str:
        return validate_password_complexity(value)


class GoogleUserRegister(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    user_type: UserType = UserType.USER
    google_subject: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleUserLoginRequest(BaseModel):
    email: EmailStr
    google_subject: str


class UserLoginResponse(BaseModel):
    first_name: str
    last_name: str
    access_token: str
    token_type: str


class Token(BaseModel):
    access_token: str
    token_type: str


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=1)


class EmailVerificationRequest(BaseModel):
    token: str = Field(min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password_complexity(cls, value: str) -> str:
        return validate_password_complexity(value)


class GoogleLinkResponse(BaseModel):
    success: bool
    message: str


class EmailChangeRequest(BaseModel):
    new_email: EmailStr
    current_password: str | None = None
    google_credential: str | None = None

    @model_validator(mode="after")
    def require_exactly_one_credential(self) -> "EmailChangeRequest":
        provided = [self.current_password, self.google_credential]
        if sum(value is not None for value in provided) != 1:
            raise ValueError(
                "Provide exactly one of current_password or google_credential."
            )
        return self


class EmailChangeConfirmRequest(BaseModel):
    token: str = Field(min_length=1)


class EmailChangeCancelRequest(BaseModel):
    token: str = Field(min_length=1)
