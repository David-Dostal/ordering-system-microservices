from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request
from typing import List
from models import Order, OrderItem  # Import your SQLAlchemy models
from database import SessionLocal, engine, Base  # Import Base from your database module

import schemas, crud, database, models
from database import SessionLocal, engine
from sqlalchemy.orm import sessionmaker
import pika
import json
import threading



# Function to create database tables
def create_database_tables():
    Base.metadata.create_all(bind=engine)


def start_rabbitmq_consumer():
    conn_params = pika.ConnectionParameters(host='rabbitmq', credentials=pika.PlainCredentials('user', 'secret'))
    conn = pika.BlockingConnection(conn_params)
    channel = conn.channel()
    channel.queue_declare(queue="orders", durable=True)

    def on_message_callback(channel, method, properties, body):
        print("Received Order:", body)
        order_data = json.loads(body)
        crud.process_order_from_message(order_data)

    channel.basic_consume(queue="orders", on_message_callback=on_message_callback, auto_ack=True)
    print("Starting consuming...")
    channel.start_consuming()

if __name__ == "__main__":
    create_database_tables()  # Create database tables
    start_rabbitmq_consumer()  # Start RabbitMQ consumer