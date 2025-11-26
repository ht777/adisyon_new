from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models import Order, OrderItem, OrderStatus, Table, Product, TableState, get_session
from auth import require_role, get_current_active_user, optional_current_user
from models import UserRole
from datetime import datetime
from websocket_utils import broadcast_order_update, broadcast_to_admin
from models import StockMovement, MovementType
from pydantic import BaseModel
import logging

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger("printer")

# Pydantic models (Diğer fonksiyonlardan eksik kalanlar)
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1
    extras: Dict[str, Any] = {}

class OrderCreate(BaseModel):
    # FIX: table_id yerine table_number kullanıldı
    table_number: int 
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

# DÜZELTME: Status artık metin (str) olarak geliyor
class OrderStatusUpdate(BaseModel):
    status: str 

# --- ENDPOINTLER ---

@router.get("/kitchen/pending")
async def get_pending_orders_for_kitchen(db: Session = Depends(get_session)):
    orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.BEKLIYOR, OrderStatus.HAZIRLANIYOR])
    ).order_by(Order.created_at.asc()).all()
    
    result = []
    for order in orders:
        items = []
        for item in order.items:
            p_name = item.product.name if item.product else "Silinmiş Ürün"
            items.append({
                "id": item.id, "product_id": item.product_id, "product_name": p_name,
                "quantity": item.quantity, "extras": item.extras, "subtotal": item.subtotal
            })
        table_name = order.table.name if order.table else "Masa Bilinmiyor"
        result.append({
            "id": order.id, "table_name": table_name, "status": order.status,
            "customer_notes": order.customer_notes, "created_at": order.created_at.isoformat(),
            "items": items, "total_amount": order.total_amount
        })
    return result

@router.get("/kitchen-tickets")
async def get_kitchen_tickets(db: Session = Depends(get_session)):
    orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.BEKLIYOR, OrderStatus.HAZIRLANIYOR])
    ).order_by(Order.created_at.asc()).all()
    result = []
    for order in orders:
        items = []
        for item in order.items:
            p_name = item.product.name if item.product else "Silinmiş Ürün"
            items.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": p_name,
                "quantity": item.quantity,
                "extras": item.extras,
                "subtotal": item.subtotal
            })
        table_name = order.table.name if order.table else "Masa Bilinmiyor"
        result.append({
            "id": order.id,
            "table_name": table_name,
            "status": order.status,
            "customer_notes": order.customer_notes,
            "created_at": order.created_at.isoformat(),
            "items": items,
            "total_amount": order.total_amount
        })
    return result

@router.post("/printer/print-order/{order_id}")
async def print_order_stub(order_id: int):
    logger.info(f"Printing order #{order_id} to ESC/POS printer")
    return {"message": f"Printing order #{order_id}"}

@router.get("/stats")
async def get_order_stats(db: Session = Depends(get_session)):
    return {"total_orders": db.query(Order).count()}

@router.post("", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: Session = Depends(get_session)):
    # FIX: Masayı table_number ile bul
    table = db.query(Table).filter(Table.number == order.table_number).first()
    if not table: raise HTTPException(status_code=404, detail=f"Table with number {order.table_number} not found")
    
    new_order = Order(table_id=table.id, customer_notes=order.customer_notes, status=OrderStatus.BEKLIYOR)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    total_amount = 0.0
    order_items = []
    for item_data in order.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product: continue
        if bool(product.track_stock or False):
            if int(product.stock or 0) < int(item_data.quantity or 0):
                raise HTTPException(status_code=400, detail=f"Yetersiz stok: {product.name} (Kalan: {int(product.stock or 0)})")
            product.stock = int(product.stock or 0) - int(item_data.quantity or 0)
            db.add(StockMovement(product_id=product.id, quantity=-int(item_data.quantity or 0), movement_type=MovementType.SATIS, description=f"Sipariş #{new_order.id} - Masa {table.number}"))
            if int(product.stock or 0) <= 15:
                await broadcast_to_admin({"type": "stock_warning", "message": f"Dikkat: {product.name} stoğu azaldı! Kalan: {int(product.stock or 0)}"})
        subtotal = product.price * item_data.quantity
        total_amount += subtotal
        order_item = OrderItem(order_id=new_order.id, product_id=item_data.product_id, quantity=item_data.quantity, unit_price=product.price, extras=item_data.extras, subtotal=subtotal)
        db.add(order_item)
        db.commit()
        db.refresh(order_item)
        order_items.append({
            "id": order_item.id, "product_id": order_item.product_id, "quantity": order_item.quantity,
            "unit_price": order_item.unit_price, "extras": order_item.extras, "subtotal": order_item.subtotal,
            "product": {"id": product.id, "name": product.name, "description": product.description, "price": product.price, "image_url": product.image_url}
        })
    
    new_order.total_amount = total_amount
    db.commit()
    # Masa occupancy set
    try:
        ts = db.query(TableState).filter(TableState.table_id == table.id).first()
        if not ts:
            ts = TableState(table_id=table.id, is_occupied=True)
            db.add(ts)
        else:
            ts.is_occupied = True
        db.commit()
    except Exception:
        db.rollback()
    
    await broadcast_order_update({
        "id": new_order.id, "table_id": new_order.table_id, "table_name": table.name, "status": new_order.status,
        "customer_notes": new_order.customer_notes, "total_amount": new_order.total_amount,
        "created_at": new_order.created_at.isoformat(),
        "items": [{"product_name": i['product']['name'], "quantity": i['quantity']} for i in order_items]
    }, "order_created")
    await broadcast_to_admin({"type": "table_status", "table_number": table.number, "table_name": table.name, "is_occupied": True, "total_amount": new_order.total_amount})
    
    return {
        "id": new_order.id, "table_id": new_order.table_id, "table_name": table.name, "status": new_order.status,
        "customer_notes": new_order.customer_notes, "total_amount": new_order.total_amount,
        "created_at": new_order.created_at, "updated_at": new_order.updated_at, "items": order_items
    }

@router.get("", response_model=List[OrderResponse])
async def get_orders(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), status_filter: Optional[OrderStatus] = Query(None), table_id: Optional[int] = Query(None), db: Session = Depends(get_session)):
    query = db.query(Order).join(Table)
    if status_filter: query = query.filter(Order.status == status_filter)
    if table_id: query = query.filter(Order.table_id == table_id)
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        items = []
        for item in order.items:
            p_name = item.product.name if item.product else "Bilinmeyen"
            p_desc = item.product.description if item.product else ""
            p_img = item.product.image_url if item.product else ""
            items.append({"id": item.id, "product_id": item.product_id, "quantity": item.quantity, "unit_price": item.unit_price, "extras": item.extras, "subtotal": item.subtotal, "product": {"id": item.product_id, "name": p_name, "description": p_desc, "price": item.unit_price, "image_url": p_img}})
        table_name = order.table.name if order.table else "Masa Bilinmiyor"
        result.append({"id": order.id, "table_id": order.table_id, "table_name": table_name, "status": order.status, "customer_notes": order.customer_notes, "total_amount": order.total_amount, "created_at": order.created_at, "updated_at": order.updated_at, "items": items})
    return result

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_session)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order: raise HTTPException(status_code=404, detail="Order not found")
    items = []
    for item in order.items:
        p_name = item.product.name if item.product else "Bilinmeyen"
        items.append({"id": item.id, "product_id": item.product_id, "quantity": item.quantity, "unit_price": item.unit_price, "extras": item.extras, "subtotal": item.subtotal, "product": {"id": item.product_id, "name": p_name, "description": "", "price": item.unit_price, "image_url": ""}})
    table_name = order.table.name if order.table else "Masa Bilinmiyor"
    return {"id": order.id, "table_id": order.table_id, "table_name": table_name, "status": order.status, "customer_notes": order.customer_notes, "total_amount": order.total_amount, "created_at": order.created_at, "updated_at": order.updated_at, "items": items}

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(optional_current_user)
):
    # ÇEVİRİ SÖZLÜĞÜ: Türkçe/İngilizce ne gelirse gelsin doğruya çevirir
    status_map = {
        "hazirlaniyor": OrderStatus.HAZIRLANIYOR, "hazırlanıyor": OrderStatus.HAZIRLANIYOR, "preparing": OrderStatus.HAZIRLANIYOR,
        "hazir": OrderStatus.HAZIR, "hazır": OrderStatus.HAZIR, "ready": OrderStatus.HAZIR,
        "teslim_edildi": OrderStatus.TESLIM_EDILDI, "delivered": OrderStatus.TESLIM_EDILDI,
        "iptal": OrderStatus.IPTAL, "cancelled": OrderStatus.IPTAL, "bekliyor": OrderStatus.BEKLIYOR, "pending": OrderStatus.BEKLIYOR
    }

    clean_status = status_update.status.lower().strip()
    new_status_enum = status_map.get(clean_status)

    if not new_status_enum:
        raise HTTPException(status_code=422, detail=f"Geçersiz durum: {status_update.status}")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order: raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = new_status_enum
    db.commit()
    try:
        if new_status_enum == OrderStatus.TESLIM_EDILDI and current_user is not None:
            from models import UserStats
            stats = db.query(UserStats).filter(UserStats.user_id == current_user.id).first()
            if not stats:
                stats = UserStats(user_id=current_user.id)
                db.add(stats)
                db.flush()
            amt = float(order.total_amount or 0.0)
            tips = 0.0
            stats.total_sales_score = float(stats.total_sales_score or 0.0) + amt
            stats.total_tips_collected = float(stats.total_tips_collected or 0.0) + tips
            db.commit()
    except Exception:
        pass
    
    table_name = order.table.name if order.table else "Masa Bilinmiyor"
    await broadcast_order_update({"id": order.id, "status": order.status, "table_name": table_name}, "order_updated")
    
    return {
        "id": order.id, "table_id": order.table_id, "table_name": table_name,
        "status": order.status, "customer_notes": order.customer_notes,
        "total_amount": order.total_amount, "created_at": order.created_at,
        "updated_at": order.updated_at, "items": []
    }
