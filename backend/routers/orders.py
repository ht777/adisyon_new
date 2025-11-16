from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Order, OrderItem, OrderStatus, Table, Product, get_session
from auth import require_role, get_current_active_user
from models import UserRole
from datetime import datetime
from websocket_utils import broadcast_order_update

router = APIRouter(prefix="/orders", tags=["Orders"])

# Pydantic models
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1
    extras: Dict[str, Any] = {}

class OrderCreate(BaseModel):
    table_id: int
    items: List[OrderItemCreate]
    customer_notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    extras: Dict[str, Any]
    subtotal: float
    product: Dict[str, Any]

class OrderResponse(BaseModel):
    id: int
    table_id: int
    table_name: str
    status: OrderStatus
    customer_notes: Optional[str]
    total_amount: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

# Order endpoints
@router.post("", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_session)
):
    # Check if table exists
    table = db.query(Table).filter(Table.id == order.table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Create order
    new_order = Order(
        table_id=order.table_id,
        customer_notes=order.customer_notes,
        status=OrderStatus.BEKLIYOR
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    total_amount = 0.0
    order_items = []
    
    # Create order items
    for item_data in order.items:
        # Check if product exists
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with id {item_data.product_id} not found")
        
        # Calculate subtotal
        subtotal = product.price * item_data.quantity
        total_amount += subtotal
        
        # Create order item
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=product.price,
            extras=item_data.extras,
            subtotal=subtotal
        )
        db.add(order_item)
        db.commit()
        db.refresh(order_item)
        
        # Add product info for response
        order_items.append({
            "id": order_item.id,
            "product_id": order_item.product_id,
            "quantity": order_item.quantity,
            "unit_price": order_item.unit_price,
            "extras": order_item.extras,
            "subtotal": order_item.subtotal,
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "image_url": product.image_url
            }
        })
    
    # Update order total
    new_order.total_amount = total_amount
    db.commit()
    
    # Broadcast order creation to kitchen and admin
    order_data = {
        "id": new_order.id,
        "table_id": new_order.table_id,
        "table_name": table.name,
        "status": new_order.status,
        "customer_notes": new_order.customer_notes,
        "total_amount": new_order.total_amount,
        "created_at": new_order.created_at.isoformat(),
        "items": order_items
    }
    
    broadcast_order_update(order_data, "order_created")
    
    return {
        "id": new_order.id,
        "table_id": new_order.table_id,
        "table_name": table.name,
        "status": new_order.status,
        "customer_notes": new_order.customer_notes,
        "total_amount": new_order.total_amount,
        "created_at": new_order.created_at,
        "updated_at": new_order.updated_at,
        "items": order_items
    }

@router.get("", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[OrderStatus] = Query(None),
    table_id: Optional[int] = Query(None),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_session)
):
    query = db.query(Order).join(Table)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    if table_id:
        query = query.filter(Order.table_id == table_id)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        # Get order items with product info
        items = []
        for item in order.items:
            items.append({
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "extras": item.extras,
                "subtotal": item.subtotal,
                "product": {
                    "id": item.product.id,
                    "name": item.product.name,
                    "description": item.product.description,
                    "price": item.product.price,
                    "image_url": item.product.image_url
                }
            })
        
        result.append({
            "id": order.id,
            "table_id": order.table_id,
            "table_name": order.table.name,
            "status": order.status,
            "customer_notes": order.customer_notes,
            "total_amount": order.total_amount,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": items
        })
    
    return result

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_session)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get order items with product info
    items = []
    for item in order.items:
        items.append({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "extras": item.extras,
            "subtotal": item.subtotal,
            "product": {
                "id": item.product.id,
                "name": item.product.name,
                "description": item.product.description,
                "price": item.product.price,
                "image_url": item.product.image_url
            }
        })
    
    return {
        "id": order.id,
        "table_id": order.table_id,
        "table_name": order.table.name,
        "status": order.status,
        "customer_notes": order.customer_notes,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": items
    }

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.KITCHEN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update status
    order.status = status_update.status
    db.commit()
    
    # Broadcast status update
    order_data = {
        "id": order.id,
        "table_id": order.table_id,
        "table_name": order.table.name,
        "status": order.status,
        "customer_notes": order.customer_notes,
        "total_amount": order.total_amount,
        "updated_at": order.updated_at.isoformat()
    }
    
    broadcast_order_update(order_data, "order_updated")
    
    # Get order items for response
    items = []
    for item in order.items:
        items.append({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "extras": item.extras,
            "subtotal": item.subtotal,
            "product": {
                "id": item.product.id,
                "name": item.product.name,
                "description": item.product.description,
                "price": item.product.price,
                "image_url": item.product.image_url
            }
        })
    
    return {
        "id": order.id,
        "table_id": order.table_id,
        "table_name": order.table.name,
        "status": order.status,
        "customer_notes": order.customer_notes,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": items
    }

@router.delete("/{order_id}")
async def cancel_order(
    order_id: int,
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update status to cancelled
    order.status = OrderStatus.IPTAL
    db.commit()
    
    # Broadcast cancellation
    order_data = {
        "id": order.id,
        "table_id": order.table_id,
        "table_name": order.table.name,
        "status": order.status,
        "updated_at": order.updated_at.isoformat()
    }
    
    broadcast_order_update(order_data, "order_cancelled")
    
    return {"message": "Order cancelled successfully"}

# Kitchen-specific endpoints
@router.get("/kitchen/pending")
async def get_pending_orders_for_kitchen(
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.KITCHEN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    """Get orders that need kitchen attention (bekliyor and hazirlaniyor)"""
    orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.BEKLIYOR, OrderStatus.HAZIRLANIYOR])
    ).order_by(
        Order.created_at.asc()
    ).all()
    
    result = []
    for order in orders:
        items = []
        for item in order.items:
            items.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "extras": item.extras,
                "subtotal": item.subtotal
            })
        
        result.append({
            "id": order.id,
            "table_name": order.table.name,
            "status": order.status,
            "customer_notes": order.customer_notes,
            "created_at": order.created_at.isoformat(),
            "items": items,
            "total_amount": order.total_amount
        })
    
    return result

@router.get("/stats")
async def get_order_stats(
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    """Get order statistics for dashboard"""
    
    # Total orders
    total_orders = db.query(Order).count()
    
    # Active orders (not delivered or cancelled)
    active_orders = db.query(Order).filter(
        ~Order.status.in_([OrderStatus.TESLIM_EDILDI, OrderStatus.IPTAL])
    ).count()
    
    # Orders by status
    orders_by_status = {}
    for status in OrderStatus:
        count = db.query(Order).filter(Order.status == status).count()
        orders_by_status[status.value] = count
    
    # Today's orders
    from datetime import date
    today = date.today()
    today_orders = db.query(Order).filter(
        Order.created_at >= today
    ).count()
    
    # Today's revenue
    today_revenue = db.query(Order).filter(
        Order.created_at >= today,
        Order.status == OrderStatus.TESLIM_EDILDI
    ).all()
    
    today_revenue_amount = sum(order.total_amount for order in today_revenue)
    
    return {
        "total_orders": total_orders,
        "active_orders": active_orders,
        "orders_by_status": orders_by_status,
        "today_orders": today_orders,
        "today_revenue": today_revenue_amount,
        "last_updated": datetime.now().isoformat()
    }