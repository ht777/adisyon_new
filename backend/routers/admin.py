from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User, Product, Category, Order, Table, OrderItem, OrderStatus, RestaurantConfig, get_session
from auth import require_role, get_current_active_user
from models import UserRole
from datetime import datetime, date, timedelta
from sqlalchemy import func

router = APIRouter(prefix="/admin", tags=["Admin"])

# --- MODELLER ---

class SettingsUpdate(BaseModel):
    restaurant_name: str
    currency: str
    tax_rate: float
    service_charge: float
    wifi_password: Optional[str] = None
    order_timeout_minutes: int

# --- ENDPOINTLER ---

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    # Date calculations
    today_date = date.today()
    today_start = datetime.combine(today_date, datetime.min.time())
    today_end = datetime.combine(today_date, datetime.max.time())
    
    # Sayaçlar
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_tables = db.query(Table).filter(Table.is_active == True).count()
    
    # Bugünün siparişleri (Herhangi bir statüdeki)
    today_orders_query = db.query(Order).filter(Order.created_at >= today_start, Order.created_at <= today_end)
    today_order_count = today_orders_query.count()
    
    # Bugünün cirosu (FIXED: HAZIR ve TESLIM_EDILDI statülerini dahil et)
    today_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= today_start,
        Order.created_at <= today_end,
        Order.status.in_([OrderStatus.TESLIM_EDILDI, OrderStatus.HAZIR])
    ).scalar() or 0.0
    
    # Aktif siparişler (FIXED: Sadece BEKLIYOR ve HAZIRLANIYOR sayılır)
    active_orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.BEKLIYOR, OrderStatus.HAZIRLANIYOR])
    ).count()
    
    # Haftalık Satış Grafiği Verisi
    daily_trend = []
    for i in range(6, -1, -1):
        day_date = today_date - timedelta(days=i)
        day_start_range = datetime.combine(day_date, datetime.min.time())
        day_end_range = datetime.combine(day_date, datetime.max.time())
        
        # Ciro hesaplaması HAZIR ve TESLİM EDİLDİ için
        day_rev = db.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= day_start_range,
            Order.created_at <= day_end_range,
            Order.status.in_([OrderStatus.TESLIM_EDILDI, OrderStatus.HAZIR])
        ).scalar() or 0.0
        daily_trend.append({"date": day_date.isoformat(), "revenue": day_rev})

    return {
        "overview": {
            "total_products": total_products,
            "total_tables": total_tables,
        },
        "sales": {
            "today_orders": today_order_count,
            "today_revenue": today_revenue,
            "active_orders": active_orders,
            "daily_trend": daily_trend
        }
    }

@router.get("/reports/sales")
async def get_sales_report(
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    if not start_date: start_date = date.today() - timedelta(days=30)
    if not end_date: end_date = date.today()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # FIXED: Rapor için de HAZIR ve TESLİM EDİLDİ statülerini dahil et
    orders = db.query(Order).filter(
        Order.created_at >= start_datetime,
        Order.created_at <= end_datetime,
        Order.status.in_([OrderStatus.TESLIM_EDILDI, OrderStatus.HAZIR])
    ).all()
    
    total_revenue = sum(o.total_amount for o in orders)
    total_count = len(orders)
    
    # Günlük kırılım
    breakdown = {}
    for o in orders:
        d = o.created_at.date().isoformat()
        if d not in breakdown: breakdown[d] = {"revenue": 0, "count": 0}
        breakdown[d]["revenue"] += o.total_amount
        breakdown[d]["count"] += 1
        
    # En çok satan ürünler (Bu tarih aralığında)
    product_stats = {}
    order_ids = [o.id for o in orders]
    if order_ids:
        items = db.query(OrderItem).join(Product).filter(OrderItem.order_id.in_(order_ids)).all()
        for item in items:
            if not item.product: continue
            pid = item.product_id
            if pid not in product_stats:
                product_stats[pid] = {"name": item.product.name, "qty": 0, "total": 0}
            product_stats[pid]["qty"] += item.quantity
            product_stats[pid]["total"] += item.subtotal

    top_products = sorted(product_stats.values(), key=lambda x: x["total"], reverse=True)[:10]

    return {
        "total_revenue": total_revenue,
        "total_orders": total_count,
        "average_order": total_revenue / total_count if total_count > 0 else 0,
        "daily_breakdown": [{"date": k, **v, "orders": v["count"]} for k, v in sorted(breakdown.items())],
        "top_products": top_products
    }

@router.get("/settings")
async def get_system_settings(db: Session = Depends(get_session)):
    config = db.query(RestaurantConfig).first()
    if not config:
        config = RestaurantConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.put("/settings")
async def update_system_settings(
    settings: SettingsUpdate,
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    config = db.query(RestaurantConfig).first()
    if not config:
        config = RestaurantConfig()
        db.add(config)
    
    config.restaurant_name = settings.restaurant_name
    config.currency = settings.currency
    config.tax_rate = settings.tax_rate
    config.service_charge = settings.service_charge
    config.wifi_password = settings.wifi_password
    config.order_timeout_minutes = settings.order_timeout_minutes
    
    db.commit()
    return {"message": "Ayarlar başarıyla güncellendi"}