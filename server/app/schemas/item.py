from typing import Optional
from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    category: Optional[str] = None

class ItemResponse(ItemCreate):
    id: int

    class Config:
        from_attributes = True