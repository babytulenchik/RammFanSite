from sqlalchemy.orm import Session
from models import Cart, CartItem, Product
import uuid
from typing import Dict, List, Optional

class CartManager:
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_cart(self, session_id: str) -> Cart:
        cart = self.db.query(Cart).filter(Cart.id == session_id).first()
        
        if not cart:
            cart = Cart(id=session_id)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        
        return cart
    
    def add_to_cart(self, session_id: str, product_id: int, quantity: int = 1) -> Dict:
        cart = self.get_or_create_cart(session_id)
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            return {"success": False, "error": "Product not found"}
        
        if product.stock < quantity:
            return {"success": False, "error": "Not enough stock"}
        
        cart_item = self.db.query(CartItem).filter(
            CartItem.cart_id == session_id,
            CartItem.product_id == product_id
        ).first()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                cart_id=session_id,
                product_id=product_id,
                quantity=quantity
            )
            self.db.add(cart_item)
        
        self.db.commit()
        
        return {
            "success": True,
            "cart_item_id": cart_item.id,
            "product_name": product.name,
            "quantity": cart_item.quantity
        }
    
    def update_cart_item(self, session_id: str, item_id: int, quantity: int) -> Dict:
        cart_item = self.db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.cart_id == session_id
        ).first()
        
        if not cart_item:
            return {"success": False, "error": "Item not found in cart"}
        
        product = self.db.query(Product).filter(Product.id == cart_item.product_id).first()
        
        if quantity <= 0:
            self.db.delete(cart_item)
            action = "removed"
        else:
            if product and product.stock < quantity:
                return {"success": False, "error": "Not enough stock"}
            cart_item.quantity = quantity
            action = "updated"
        
        self.db.commit()
        
        return {
            "success": True,
            "action": action,
            "item_id": item_id,
            "quantity": quantity
        }
    
    def remove_from_cart(self, session_id: str, item_id: int) -> Dict:
        cart_item = self.db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.cart_id == session_id
        ).first()
        
        if cart_item:
            self.db.delete(cart_item)
            self.db.commit()
            return {"success": True, "item_id": item_id}
        
        return {"success": False, "error": "Item not found"}
    
    def get_cart_details(self, session_id: str) -> Dict:
        cart = self.get_or_create_cart(session_id)
        cart_items = self.db.query(CartItem).filter(CartItem.cart_id == session_id).all()
        
        items = []
        subtotal = 0
        total_items = 0
        
        for item in cart_items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                item_total = product.price * item.quantity
                items.append({
                    "id": item.id,
                    "product_id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "quantity": item.quantity,
                    "total": item_total,
                    "image_url": product.image_url,
                    "stock": product.stock
                })
                subtotal += item_total
                total_items += item.quantity
        
        from config import config
        
        shipping = 0 if subtotal >= config.FREE_SHIPPING_THRESHOLD else config.SHIPPING_COST
        total = subtotal + shipping
        
        return {
            "session_id": session_id,
            "items": items,
            "total_items": total_items,
            "item_count": len(items),
            "subtotal": round(subtotal, 2),
            "shipping": shipping,
            "total": round(total, 2),
            "free_shipping_threshold": config.FREE_SHIPPING_THRESHOLD,
            "has_free_shipping": shipping == 0
        }
    
    def clear_cart(self, session_id: str) -> Dict:
        deleted_count = self.db.query(CartItem).filter(CartItem.cart_id == session_id).delete()
        self.db.commit()
        
        return {
            "success": True,
            "deleted_items": deleted_count,
            "session_id": session_id
        }