from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from utils.databases import get_db
from models.order import Order
from models.product import Product
from schemas.order import OrderCreate, OrderResponse
from dsa.queue import Queue

router = APIRouter(prefix="/orders", tags=["Orders"])

#order processing queue
order_queue = Queue()

@router.post("/", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Calculate total price and validate products
    total_price = 0.0
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        total_price += product.price * item.quantity
    
    # Create order in database
    db_order = Order(
        user_id=order.user_id,
        restaurant_id=order.restaurant_id,
        items=[item.dict() for item in order.items],
        status="pending"
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Add to processing queue
    order_queue.enqueue(db_order.id)
    
    return OrderResponse.from_orm(db_order)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse.from_orm(order)