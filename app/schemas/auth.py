from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserType


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    user_type: UserType = UserType.USER


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
    new_password: str = Field(min_length=8)


class GoogleLinkResponse(BaseModel):
    success: bool
    message: str
