from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User, Product, Category, Order, Table, ExtraGroup, ExtraItem, OrderStatus, OrderItem, get_session
from auth import require_role, get_current_active_user
from models import UserRole
from datetime import datetime, date, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])

# Dashboard statistics
@router.get("/dashboard")
async def get_dashboard_stats(
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    """Get comprehensive dashboard statistics"""
    
    # Date calculations
    today = date.today()
    yesterday = today - timedelta(days=1)
    this_week_start = today - timedelta(days=today.weekday())
    this_month_start = date(today.year, today.month, 1)
    
    # Basic counts
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_categories = db.query(Category).filter(Category.is_active == True).count()
    total_tables = db.query(Table).filter(Table.is_active == True).count()
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # Order statistics
    total_orders = db.query(Order).count()
    
    # Today's orders
    today_orders = db.query(Order).filter(
        Order.created_at >= today
    ).count()
    
    # Today's revenue
    today_revenue = db.query(Order).filter(
        Order.created_at >= today,
        Order.status == OrderStatus.TESLIM_EDILDI
    ).all()
    today_revenue_amount = sum(order.total_amount for order in today_revenue)
    
    # Active orders (not delivered or cancelled)
    active_orders = db.query(Order).filter(
        ~Order.status.in_([OrderStatus.TESLIM_EDILDI, OrderStatus.IPTAL])
    ).count()
    
    # Orders by status
    orders_by_status = {}
    for status in OrderStatus:
        count = db.query(Order).filter(Order.status == status).count()
        orders_by_status[status.value] = count
    
    # Top selling products (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    
    # This is a simplified version - in a real app you'd want to join OrderItem with Product
    # and aggregate by product_id
    recent_orders = db.query(Order).filter(
        Order.created_at >= thirty_days_ago
    ).all()
    
    product_sales = {}
    for order in recent_orders:
        for item in order.items:
            product_name = item.product.name
            product_sales[product_name] = product_sales.get(product_name, 0) + item.quantity
    
    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Daily sales trend (last 7 days)
    daily_sales = []
    for i in range(7):
        day = today - timedelta(days=i)
        day_orders = db.query(Order).filter(
            Order.created_at >= day,
            Order.created_at < day + timedelta(days=1),
            Order.status == OrderStatus.TESLIM_EDILDI
        ).all()
        day_revenue = sum(order.total_amount for order in day_orders)
        daily_sales.append({
            "date": day.isoformat(),
            "revenue": day_revenue,
            "orders": len(day_orders)
        })
    
    return {
        "overview": {
            "total_products": total_products,
            "total_categories": total_categories,
            "total_tables": total_tables,
            "total_users": total_users,
            "total_orders": total_orders
        },
        "sales": {
            "today_orders": today_orders,
            "today_revenue": today_revenue_amount,
            "active_orders": active_orders,
            "daily_trend": daily_sales
        },
        "orders_by_status": orders_by_status,
        "top_products": [
            {"name": name, "quantity_sold": quantity}
            for name, quantity in top_products
        ],
        "last_updated": datetime.now().isoformat()
    }

# User management
@router.get("/users")
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    """Get all users with pagination"""
    users = db.query(User).offset(skip).limit(limit).all()
    
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ],
        "total": db.query(User).count()
    }

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    """Update user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    db.commit()
    
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    """Update user role"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    db.commit()
    
    return {"message": f"User role updated to {role} successfully"}

# System settings
@router.get("/settings")
async def get_system_settings(
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    """Get system settings"""
    # This is a placeholder - in a real app you'd have a Settings table
    return {
        "restaurant_name": "Restaurant Order System",
        "currency": "TRY",
        "tax_rate": 0.18,
        "service_charge": 0.0,
        "timezone": "Europe/Istanbul",
        "language": "tr",
        "order_timeout_minutes": 30
    }

@router.put("/settings")
async def update_system_settings(
    settings: Dict[str, Any],
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    """Update system settings"""
    # This is a placeholder - in a real app you'd update a Settings table
    return {"message": "Settings updated successfully"}

# Reports
@router.get("/reports/sales")
async def get_sales_report(
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    """Get sales report for date range"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    # Get orders in date range
    orders = db.query(Order).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date + timedelta(days=1),
        Order.status == OrderStatus.TESLIM_EDILDI
    ).all()
    
    total_revenue = sum(order.total_amount for order in orders)
    total_orders = len(orders)
    
    # Daily breakdown
    daily_breakdown = {}
    for order in orders:
        order_date = order.created_at.date()
        if order_date not in daily_breakdown:
            daily_breakdown[order_date] = {"revenue": 0, "orders": 0}
        daily_breakdown[order_date]["revenue"] += order.total_amount
        daily_breakdown[order_date]["orders"] += 1
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "average_order_value": total_revenue / total_orders if total_orders > 0 else 0,
        "daily_breakdown": [
            {"date": date.isoformat(), "revenue": data["revenue"], "orders": data["orders"]}
            for date, data in sorted(daily_breakdown.items())
        ]
    }

@router.get("/reports/products")
async def get_products_report(
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    """Get products performance report"""
    
    # Get all products with their sales data
    products = db.query(Product).filter(Product.is_active == True).all()
    
    product_stats = []
    for product in products:
        # Get total quantity sold and revenue for this product
        order_items = db.query(OrderItem).join(Order).filter(
            OrderItem.product_id == product.id,
            Order.status == OrderStatus.TESLIM_EDILDI
        ).all()
        
        total_quantity = sum(item.quantity for item in order_items)
        total_revenue = sum(item.subtotal for item in order_items)
        
        product_stats.append({
            "id": product.id,
            "name": product.name,
            "category": product.category.name,
            "price": product.price,
            "total_quantity_sold": total_quantity,
            "total_revenue": total_revenue,
            "is_featured": product.is_featured
        })
    
    # Sort by revenue
    product_stats.sort(key=lambda x: x["total_revenue"], reverse=True)
    
    return {
        "products": product_stats,
        "generated_at": datetime.now().isoformat()
    }

# Backup and maintenance
@router.post("/backup/create")
async def create_backup(
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    """Create database backup"""
    # This is a placeholder - in a real app you'd implement proper backup logic
    return {"message": "Backup created successfully", "backup_id": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}

@router.get("/system/health")
async def get_system_health(
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    """Get system health status"""
    
    # Database health
    db_healthy = True
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False
    
    # Get system info
    try:
        import psutil
        has_psutil = True
    except ImportError:
        has_psutil = False
    
    system_info = {"status": "unknown"}
    if has_psutil:
        try:
            system_info = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except Exception:
            system_info = {"status": "error"}
    
    return {
        "database": "healthy" if db_healthy else "unhealthy",
        "system": system_info,
        "timestamp": datetime.now().isoformat()
    }