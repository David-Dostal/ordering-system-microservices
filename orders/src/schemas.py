from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List

class OrderItemBase(BaseModel):
    item_id: str
    quantity: int
    unit_price: float

class OrderItemCreate(BaseModel):
    item_id: str
    quantity: int
    unit_price: float

class OrderItem(BaseModel):
    item_id: str
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItemCreate]
    total_price: float
    address: str

class Order(BaseModel):
    user_id: str
    items: List[OrderItem]
    total_price: float
    address: str


class OrderBase(BaseModel):
    user_id: str
    total_price: float
    address: str

    class Config:
        allow_population_by_field_name = True
