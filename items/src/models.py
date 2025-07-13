from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


class Item(BaseModel):
    name: str
    count: int
    reserved: int
    price_per_unit: float
    description: str
    category: str
    available: bool

class CartItem(BaseModel):
    item_id: str
    name: str
    count: int
    reserved: int
    price_per_unit: float
    description: str
    category: str
    available: bool

class Cart(BaseModel):
    user_id: str
    items: List[CartItem]
    total_price: float = Field(default=0.0)

class OrderAddress(BaseModel):
    address: str