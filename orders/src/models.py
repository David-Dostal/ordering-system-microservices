from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4
import datetime

from database import Base



class Order(Base):
    __tablename__ = 'orders'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False)
    total_price = Column(Float, nullable=False)
    order_date = Column(DateTime, default=datetime.datetime.utcnow)
    address = Column(String, nullable=False)

    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    order_id = Column(String, ForeignKey('orders.id'), nullable=False)
    item_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")