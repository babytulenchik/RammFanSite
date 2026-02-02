from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uuid
from database import get_db
from shop.cart_logic import CartManager
from config import config
from models import Product

router = APIRouter(prefix="/shop", tags=["shop"])
templates = Jinja2Templates(directory="templates")

def get_session_id(request: Request) -> str:
    session_id = request.cookies.get(config.SESSION_COOKIE_NAME)
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.get("/merchandise", response_class=HTMLResponse)
async def merchandise_page(request: Request, db: Session = Depends(get_db)):
    from models import Product
    products = db.query(Product).all()
    
    return templates.TemplateResponse(
        "merchandise.html",
        {"request": request, "products": products}
    )

@router.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    return templates.TemplateResponse("cart.html", {"request": request})

@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request):
    return templates.TemplateResponse("checkout.html", {"request": request})

@router.get("/api/products")
async def get_products(db: Session = Depends(get_db)):
    """Получаем все товары"""
    from models import Product
    products = db.query(Product).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "description": p.description,
            "price": p.price,
            "image_url": p.image_url,
            "stock": p.stock
        }
        for p in products
    ]

@router.post("/api/cart/add")
async def add_to_cart_api(
    request: Request,
    product_id: int = Form(...),
    quantity: int = Form(1),
    db: Session = Depends(get_db)
):
    session_id = get_session_id(request)
    cart_manager = CartManager(db)
    
    result = cart_manager.add_to_cart(session_id, product_id, quantity)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    cart_details = cart_manager.get_cart_details(session_id)
    
    response = JSONResponse({
        "success": True,
        "message": f"{result['product_name']} added to cart",
        "cart": cart_details
    })
    
    if not request.cookies.get(config.SESSION_COOKIE_NAME):
        response.set_cookie(
            key=config.SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=config.SESSION_MAX_AGE
        )
    
    return response

@router.get("/api/cart")
async def get_cart_api(request: Request, db: Session = Depends(get_db)):
    session_id = get_session_id(request)
    cart_manager = CartManager(db)
    
    cart_details = cart_manager.get_cart_details(session_id)
    
    response = JSONResponse(cart_details)
    
    if not request.cookies.get(config.SESSION_COOKIE_NAME):
        response.set_cookie(
            key=config.SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=config.SESSION_MAX_AGE
        )
    
    return response

@router.put("/api/cart/update/{item_id}")
async def update_cart_item_api(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db)
):
    session_id = get_session_id(request)
    cart_manager = CartManager(db)
    
    try:
        data = await request.json()
        quantity = data.get("quantity", 1)
    except:
        quantity = 1
    
    result = cart_manager.update_cart_item(session_id, item_id, quantity)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    cart_details = cart_manager.get_cart_details(session_id)
    
    return JSONResponse({
        "success": True,
        "message": f"Item {result['action']} successfully",
        "cart": cart_details
    })

@router.delete("/api/cart/remove/{item_id}")
async def remove_cart_item_api(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db)
):
    session_id = get_session_id(request)
    cart_manager = CartManager(db)
    
    result = cart_manager.remove_from_cart(session_id, item_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    cart_details = cart_manager.get_cart_details(session_id)
    
    return JSONResponse({
        "success": True,
        "message": "Item removed from cart",
        "cart": cart_details
    })

@router.delete("/api/cart/clear")
async def clear_cart_api(request: Request, db: Session = Depends(get_db)):
    session_id = get_session_id(request)
    cart_manager = CartManager(db)
    
    result = cart_manager.clear_cart(session_id)
    
    return JSONResponse({
        "success": True,
        "message": "Cart cleared successfully",
        "deleted_items": result["deleted_items"]
    })

@router.post("/api/order/create")
async def create_order_api(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    db: Session = Depends(get_db)
):
    from models import Order, OrderItem
    from datetime import datetime
    
    session_id = get_session_id(request)
    cart_manager = CartManager(db)
    
    cart_details = cart_manager.get_cart_details(session_id)
    
    if cart_details["item_count"] == 0:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    order_number = f"RST-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    order = Order(
        order_number=order_number,
        customer_name=name,
        customer_email=email,
        customer_phone=phone,
        total_amount=cart_details["total"],
        status="pending"
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    for item in cart_details["items"]:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            product_name=item["name"],
            quantity=item["quantity"],
            price=item["price"]
        )
        db.add(order_item)
        
        product = db.query(Product).filter(Product.id == item["product_id"]).first()
        if product:
            product.stock -= item["quantity"]
            if product.stock < 0:
                product.stock = 0
    
    cart_manager.clear_cart(session_id)
    
    db.commit()
    
    return JSONResponse({
        "success": True,
        "order_number": order_number,
        "order_id": order.id,
        "total": cart_details["total"],
        "message": "Order created successfully"
    })

@router.get("/api/debug/session")
async def debug_session_api(request: Request, db: Session = Depends(get_db)):
    session_id = get_session_id(request)
    
    from models import Cart
    cart = db.query(Cart).filter(Cart.id == session_id).first()
    
    return {
        "session_id": session_id,
        "has_cookie": config.SESSION_COOKIE_NAME in request.cookies,
        "cookie_value": request.cookies.get(config.SESSION_COOKIE_NAME),
        "has_cart": cart is not None,
        "cart_items": len(cart.items) if cart else 0
    }