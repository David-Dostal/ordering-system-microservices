from fastapi import APIRouter, Depends, Request
from .database import db
from .models import Item, Cart, CartItem, OrderAddress
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
from bson import json_util
from .rabbitmq import publish
import grpc
from . import orders_pb2
from . import orders_pb2_grpc
from bson import ObjectId
from fastapi import HTTPException





router = APIRouter()
templates = Jinja2Templates(directory="templates")



def get_current_user(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user



@router.get('/items', response_class=HTMLResponse)
async def get_items(request: Request, user: dict = Depends(get_current_user)):
    items = list(db['items'].find())
    return templates.TemplateResponse("items.html", {"request": request, "items": items, "user": user})


@router.get('/items/category/{category_name}')
async def get_items_by_category(category_name: str) -> list[Item]:
    query = {"category": category_name}
    return list(db['items'].find(query))


@router.post('/new-item', status_code=201)
async def post_item(item: Item):
    response = db['items'].insert_one(item.dict())
    return {"id": str(response.inserted_id)}

@router.put('/item/{item_id}', status_code=200)
async def update_item(item_id: str, item: Item):
    # Convert the item_id to an ObjectId for querying
    query = {"_id": ObjectId(item_id)}

    # Update the item
    response = db['items'].replace_one(query, item.dict())

    if response.modified_count == 1:
        return {"message": "Item updated successfully"}
    else:
        # Handle case where item does not exist
        return {"error": "Item not found or no update made"}

@router.delete('/item/{item_id}', status_code=200)
async def delete_item(item_id: str):
    # Convert the item_id to an ObjectId for querying
    query = {"_id": ObjectId(item_id)}

    # Delete the item
    response = db['items'].delete_one(query)

    if response.deleted_count == 1:
        return {"message": "Item deleted successfully"}
    else:
        # Handle case where item does not exist
        return {"error": "Item not found"}
    
    # Manage carts
@router.post('/cart/add', status_code=201)
async def add_to_cart(cart: Cart):
    # Check if the user's cart already exists
    existing_cart = db['carts'].find_one({"user_id": cart.user_id})

    if existing_cart:
        # Update existing cart
        db['carts'].update_one({"user_id": cart.user_id}, {"$set": {"items": cart.items}})
        return {"message": "Cart updated"}
    else:
        # Create new cart
        db['carts'].insert_one(cart.dict())

        return {"message": "Cart created"}

from fastapi import HTTPException

from fastapi.encoders import jsonable_encoder

@router.get('/cart', response_class=HTMLResponse)
async def get_cart(request: Request, user: dict = Depends(get_current_user)):
    user_id = user['sub']
    cart = db['carts'].find_one({"user_id": user_id})
    if not cart:
        cart = {"user_id": user_id, "items": [], "total_price": 0.0}
    else:
        # Serialize the cart, including ObjectId fields
        cart = json.loads(json_util.dumps(cart))

        print(cart)  # Debug: Print the cart structure


    return templates.TemplateResponse("cart.html", {"request": request, "user": user, "cart": cart})

@router.delete('/cart')
async def clear_cart(request: Request, user: dict = Depends(get_current_user)):
    user_id = user['sub']
    cart = db['carts'].find_one({"user_id": user_id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Iterate over items in the cart and update inventory
    for cart_item in cart['items']:
        item_id = cart_item['item_id']
        quantity = cart_item['count']
        item = db['items'].find_one({"_id": ObjectId(item_id)})
        if item:
            # Update the count and reserved
            db['items'].update_one({"_id": ObjectId(item_id)}, {
                "$set": {"count": item['count'] + quantity, "reserved": item['reserved'] - quantity}
            })

    # Delete the cart after restoring item counts
    db['carts'].delete_one({"user_id": user_id})
    return {"message": "Cart cleared and items restored"}


@router.post('/cart/item/add/{item_id}/{quantity}', status_code=201)
async def add_item_to_cart(item_id: str, quantity: int, user: dict = Depends(get_current_user)):
    user_id = user['sub']
    item = db['items'].find_one({"_id": ObjectId(item_id)})
    if not item or item['count'] < quantity:
        raise HTTPException(status_code=400, detail="Item not available or insufficient stock")

    # Update the item count and reserved in the inventory
    db['items'].update_one({"_id": ObjectId(item_id)}, {
        "$set": {"count": item['count'] - quantity, "reserved": item['reserved'] + quantity}
    })

    # Update the cart
    cart = db['carts'].find_one({"user_id": user_id})
    if cart:
        # Check if item is already in the cart
        existing_item = next((i for i in cart['items'] if i['item_id'] == item_id), None)
        if existing_item:
            existing_item['count'] += quantity
        else:
            # Construct a CartItem with full item details
            cart_item = CartItem(
                item_id=item_id,
                name=item['name'],
                count=quantity,
                reserved=item['reserved'],
                price_per_unit=item['price_per_unit'],
                description=item['description'],
                category=item['category'],
                available=item['available']
            ).dict()
            cart['items'].append(cart_item)
        db['carts'].update_one({"user_id": user_id}, {"$set": {"items": cart['items']}})
    else:
        # Create new cart
        new_cart = Cart(user_id=user_id, items=[CartItem(
            item_id=item_id,
            name=item['name'],
            count=quantity,  # Note: count here refers to quantity in cart
            reserved=item['reserved'],
            price_per_unit=item['price_per_unit'],
            description=item['description'],
            category=item['category'],
            available=item['available']
        ).dict()])
        db['carts'].insert_one(new_cart.dict())
    return {"message": "Item added to cart"}

@router.post("/create-order", response_class=HTMLResponse)
async def create_order(request: Request, order_address: OrderAddress, user: dict = Depends(get_current_user)):
    user_id = user['sub']
    cart = db['carts'].find_one({"user_id": user_id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Preparing order items and calculating total price
    order_items = [
        {
            "item_id": item["item_id"],
            "quantity": item["count"],  # Quantity in cart
            "unit_price": item["price_per_unit"],
        }
        for item in cart.get("items", [])
    ]
    total_price = sum(item["unit_price"] * item["quantity"] for item in order_items)

    # Creating the order object
    order = {
        "user_id": user_id,
        "items": order_items,
        "total_price": total_price,
        "address": order_address.address
    }

    # Subtracting reserved items from the inventory
    for cart_item in cart['items']:
        item_id = cart_item['item_id']
        quantity = cart_item['count']
        item = db['items'].find_one({"_id": ObjectId(item_id)})
        if item:
            db['items'].update_one({"_id": ObjectId(item_id)}, {
                "$inc": {"reserved": -quantity}
            })

    # Sending order to RabbitMQ and clearing the cart
    order_json = json.dumps(order)
    publish(order_json)
    db['carts'].delete_one({"user_id": user_id})

    return templates.TemplateResponse("orders.html", {"request": request, "user": user})


@router.get("/orders", response_class=HTMLResponse)
async def get_user_orders(request: Request, user: dict = Depends(get_current_user)):
    user_id = user['sub']
    with grpc.insecure_channel("grpc-server:50051") as channel:
        stub = orders_pb2_grpc.OrderServiceStub(channel)
        try:
            response = stub.GetUserOrders(orders_pb2.UserOrderRequest(user_id=user_id))
        except grpc.RpcError as e:
            # Handle gRPC errors
            status_code = e.code()
            if status_code == grpc.StatusCode.NOT_FOUND:
                raise HTTPException(status_code=404, detail="No orders found for this user.")
            else:
                raise HTTPException(status_code=500, detail="Internal server error")

        # Convert gRPC response to JSON format
        orders = [{
            "id": order.id,
            "user_id": order.user_id,
            "total_price": order.total_price,
            "address": order.address,
            "items": [{
                "item_id": item.item_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price
            } for item in order.items],
            "order_date": order.order_date
        } for order in response.orders]

        # Return the template response
        return templates.TemplateResponse("orders.html", {"request": request, "user": user, "orders": orders})
