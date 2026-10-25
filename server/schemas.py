from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id:int
    image_file: str | None
    image_path: str 


class ReceiptBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=100)

class ReceiptCreate(ReceiptBase):
    user_id: int

class ReceiptResponse(ReceiptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date_bought: datetime
    author: UserResponse


