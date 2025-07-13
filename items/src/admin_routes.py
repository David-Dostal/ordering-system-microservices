from fastapi import APIRouter, Request, Form, Depends
from .database import db
from .models import Item
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import json_util
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException






router = APIRouter()
templates = Jinja2Templates(directory="templates")



def get_current_user(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user



@router.get("/admin/items", response_class=HTMLResponse)
async def admin_items(request: Request, user: dict = Depends(get_current_user)):
    items = list(db['items'].find())
    return templates.TemplateResponse("admin_items.html", {"request": request, "items": items, "user": user})

@router.post("/admin/update-item/{item_id}")
async def update_item(item_id: str, name: str = Form(...), price_per_unit: float = Form(...), count: int = Form(...), reserved: int = Form(...), description: Optional[str] = Form(""),
                       category: str = Form(...), available: Optional[bool] = Form(False), user: dict = Depends(get_current_user)):
    db['items'].update_one({"_id": ObjectId(item_id)}, {"$set": {"name": name, "price_per_unit": price_per_unit, "count": count, "reserved": reserved,
                                                                 "description": description, "category": category, "available": available}})
    return RedirectResponse(url="/admin/items", status_code=302)

@router.get("/admin/delete-item/{item_id}")
async def delete_item(item_id: str, user: dict = Depends(get_current_user)):
    db['items'].delete_one({"_id": ObjectId(item_id)})
    return RedirectResponse(url="/admin/items", status_code=302)


@router.get('/admin/new-item', response_class=HTMLResponse)
async def get_new_item_form(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("admin_new_item.html", {"request": request, "user": user})



@router.post('/admin/new-item', status_code=303)  # Use status code 303 for redirection after form submission
async def post_item(
    name: str = Form(...),
    price_per_unit: float = Form(...),
    count: int = Form(...),
    reserved: int = Form(0),
    description: str = Form(""),
    category: str = Form(...),
    available: bool = Form(False),
    user: dict = Depends(get_current_user)
):
    item_data = {
        "name": name,
        "price_per_unit": price_per_unit,
        "count": count,
        "reserved": reserved,
        "description": description,
        "category": category,
        "available": available
    }

    item = Item(**item_data)
    response = db['items'].insert_one(item.dict())
    if response.inserted_id:
        # Redirect to '/admin/items' after successful creation
        return RedirectResponse(url='/admin/items', status_code=303)
    else:
        raise HTTPException(status_code=500, detail="Item could not be added")