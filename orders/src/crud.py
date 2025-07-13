from sqlalchemy.orm import Session
import models, schemas
from uuid import uuid4
from database import SessionLocal
from schemas import OrderCreate


def insert_order(db: Session, order: schemas.OrderCreate) -> models.Order:
    db_order = models.Order(
        user_id=order.user_id,
        total_price=order.total_price,
        address=order.address
    )
    db.add(db_order)
    db.flush()  # This will assign an ID to db_order without committing the transaction

    for item in order.items:
        db_item = models.OrderItem(
            order_id=db_order.id,
            item_id=item.item_id,
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        db.add(db_item)
    
    db.commit()
    return db_order


def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).offset(skip).limit(limit).all()

def get_user_orders(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(models.Order).filter(models.Order.user_id == user_id).offset(skip).limit(limit).all()



def process_order_from_message(order_data: dict):
    db = SessionLocal()
    try:
        db.begin()
        order_schema = OrderCreate(**order_data)
        insert_order(db, order_schema)
        db.commit()
    except Exception as e:
        print(f"Error processing order: {e}")
        db.rollback()
    finally:
        db.close()