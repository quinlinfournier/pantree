from datetime import date, datetime
from pydantic import BaseModel

class BatchCreate(BaseModel):
    id: int 
    boughtDate: date
    expirationDate: date

class BatchResponse(BatchCreate):
    id: int

    class Config():
        from_attributes = True
