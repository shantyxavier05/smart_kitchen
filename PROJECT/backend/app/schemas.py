from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Inventory Item schemas
class InventoryItemCreate(BaseModel):
    name: str
    quantity: str
    category: Optional[str] = None

class InventoryItemRead(BaseModel):
    id: int
    name: str
    quantity: str
    category: Optional[str]
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# User Profile schemas
class UserAllergiesUpdate(BaseModel):
    allergies: List[str]

class UserDietaryGoalsUpdate(BaseModel):
    dietary_goals: List[str]

class UserProfileRead(BaseModel):
    allergies: List[str]
    dietary_goals: List[str]

    class Config:
        from_attributes = True

