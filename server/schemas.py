from datetime import date
from decimal import Decimal


from pydantic import BaseModel, ConfigDict, EmailStr, Field

# BASE

class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)

class ReceiptBase(BaseModel):
    retailer: str = Field(min_length=1, max_length=100)
    purchase_date: date | None = None
    currency: str = Field(min_length=1, max_length=10)
    total: Decimal = Field(ge=0)

class ReceiptItemBase(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: Decimal

# CREATE

class UserCreate(UserBase):
    pass

class ReceiptItemCreate(ReceiptItemBase):
    pass


class ReceiptCreate(ReceiptBase):
    user_id: int | None = None
    items: list[ReceiptItemCreate]


# Response

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id:int
    image_file: str | None
    image_path: str 

class ReceiptResponse(ReceiptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    retailer: str
    purchase_date: date | None = None
    currency: str
    total: Decimal

    items: list[ReceiptItemResponse]

class ReceiptItemResponse(ReceiptItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int