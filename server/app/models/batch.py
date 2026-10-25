from sqlalchemy import String, Column, Interger, DateTime, relationship
from app.core.database import Base

class BatchModel(Base):
    __tablename__ = "batchs"

    id = Column(Interger, primary_key=True, index=True)
    item_id = Column(Interger, ForeignKey("item.py"), nullable=True)
    quantity = Column(Interger, nullable=False, default=1)
    boughtDate = Column(DateTime,  nullable=True)
    expiration = Column(DateTime, nullable=True)

    item = relationship("ItemModel", backref="batches")
