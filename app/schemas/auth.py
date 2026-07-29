from pydantic import BaseModel, EmailStr
from app.models.user import UserType

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    user_type: UserType = UserType.USER 
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

    
    
class Token(BaseModel):
    access_token: str
    token_type: str
    