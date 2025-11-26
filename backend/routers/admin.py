from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User, Product, Category, Order, Table, OrderItem, OrderStatus, RestaurantConfig, StockMovement, Inventory, get_session
from services.ai_service import generate_analysis_text
from collections import defaultdict
from io import BytesIO
from fastapi.responses import FileResponse
import importlib
from auth import require_role, get_current_active_user
from models import UserRole
from datetime import datetime, date, timedelta
from sqlalchemy import func, desc
import os
import shutil
import logging

# Logger ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("admin_reports")

router = APIRouter(prefix="/admin", tags=["Admin"])

# --- MODELLER ---
class SettingsUpdate(BaseModel):
    restaurant_name: str
    currency: str
    tax_rate: float
    service_charge: float
    wifi_password: Optional[str] = None
    order_timeout_minutes: int
    logo_url: Optional[str] = None

# --- YARDIMCI FONKSİYONLAR ---
def safe_parse_date(date_val):
    """Tarih verisini her türlü formattan kurtarmaya çalışan fonksiyon"""
    if not date_val:
        return None
    
    if isinstance(date_val, datetime):
        return date_val
    
    if isinstance(date_val, str):
        try:
            return datetime.fromisoformat(date_val)
        except:
            pass
        try:
            return datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S.%f")
        except:
            pass
        try:
            return datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S")
        except:
            pass
    return None

# --- ENDPOINTLER ---

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    all_orders = db.query(Order).all()
    
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_tables = db.query(Table).filter(Table.is_active == True).count()
    
    today = date.today()
    today_order_count = 0
    today_revenue = 0.0
    active_orders = 0
    
    daily_revenue = {} 
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        daily_revenue[d] = 0.0

    for o in all_orders:
        o_dt = safe_parse_date(o.created_at)
        if not o_dt: continue
        
        o_date = o_dt.date()
        o_date_str = o_date.isoformat()
        
        status = (o.status.value if o.status else "").lower()
        is_cancelled = status in ["cancelled", "iptal"]
        is_active = status in ["pending", "preparing", "bekliyor", "hazirlaniyor"]
        
        if o_date == today:
            today_order_count += 1
            if not is_cancelled:
                today_revenue += (o.total_amount or 0.0)
        
        if is_active:
            active_orders += 1
            
        if o_date_str in daily_revenue and not is_cancelled:
            daily_revenue[o_date_str] += (o.total_amount or 0.0)

    daily_trend = [{"date": k, "revenue": v} for k, v in daily_revenue.items()]

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
    
    # EMOJİSİZ PRINT (HATA VERMEYECEK)
    print(f"[INFO] Rapor Istegi: {start_date} - {end_date}")
    
    all_orders = db.query(Order).all()
    print(f"[INFO] Veritabanindaki Toplam Siparis: {len(all_orders)}")

    filtered_orders = []
    total_revenue = 0.0
    
    breakdown = {}
    delta = end_date - start_date
    for i in range(delta.days + 1):
        day = (start_date + timedelta(days=i)).isoformat()
        breakdown[day] = {"revenue": 0, "count": 0}

    product_stats = {}
    processed_count = 0

    for o in all_orders:
        o_dt = safe_parse_date(o.created_at)
        
        if not o_dt: 
            continue
            
        o_date = o_dt.date()
        
        if start_date <= o_date <= end_date:
            processed_count += 1
            
            status = str(o.status).lower() if o.status else ""
            if status in ["cancelled", "iptal"]:
                continue
                
            filtered_orders.append(o)
            amount = o.total_amount or 0.0
            total_revenue += amount
            
            d_str = o_date.isoformat()
            if d_str in breakdown:
                breakdown[d_str]["revenue"] += amount
                breakdown[d_str]["count"] += 1
            
            for item in o.items:
                if not item.product: continue
                pid = item.product_id
                if pid not in product_stats:
                    product_stats[pid] = {"name": item.product.name, "qty": 0, "total": 0}
                
                product_stats[pid]["qty"] += item.quantity
                product_stats[pid]["total"] += (item.subtotal or 0.0)

    # EMOJİSİZ PRINTLER
    print(f"[OK] Tarih Araligina Giren: {processed_count}")
    print(f"[OK] Rapora Dahil Edilen: {len(filtered_orders)}")
    print(f"[OK] Toplam Ciro: {total_revenue}")

    top_products = sorted(product_stats.values(), key=lambda x: x["total"], reverse=True)[:10]
    daily_data = [{"date": k, **v} for k, v in sorted(breakdown.items())]

    return {
        "total_revenue": total_revenue,
        "total_orders": len(filtered_orders),
        "average_order": total_revenue / len(filtered_orders) if len(filtered_orders) > 0 else 0,
        "daily_breakdown": daily_data,
        "top_products": top_products
    }

@router.get("/reports/product-matrix")
async def product_matrix(
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    counts = defaultdict(int)
    for item in db.query(OrderItem).all():
        if item.product_id:
            counts[item.product_id] += item.quantity or 0
    products = db.query(Product).all()
    matrix = []
    vols = [counts.get(p.id, 0) for p in products]
    if vols:
        threshold = sorted(vols)[max(0, int(len(vols)*0.7)-1)]
    else:
        threshold = 0
    for p in products:
        vol = counts.get(p.id, 0)
        profit = float(p.price or 0.0)
        tag = "Star" if vol >= threshold and profit >= (p.price or 0.0)*0.5 else "Dog"
        matrix.append({"id": p.id, "name": p.name, "volume": vol, "profit_proxy": profit, "tag": tag})
    analysis = generate_analysis_text(matrix)
    return {"matrix": matrix, "analysis": analysis}

@router.get("/reports/closing-report-pdf")
async def closing_report_pdf(
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    orders = db.query(Order).all()
    total_revenue = 0.0
    for o in orders:
        status = (o.status.value if o.status else "").lower()
        if status not in ["cancelled", "iptal"]:
            total_revenue += float(o.total_amount or 0.0)
    counts = defaultdict(int)
    totals = defaultdict(float)
    for item in db.query(OrderItem).all():
        counts[item.product_id] += item.quantity or 0
        totals[item.product_id] += float(item.subtotal or 0.0)
    products = db.query(Product).all()
    top = sorted([
        {"name": p.name, "qty": counts.get(p.id, 0), "total": totals.get(p.id, 0.0)} for p in products
    ], key=lambda x: x["qty"], reverse=True)[:10]
    matrix_data = [{"name": x["name"], "volume": x["qty"], "profit_proxy": x["total"]} for x in top]
    analysis = generate_analysis_text(matrix_data)
    try:
        pagesizes = importlib.import_module("reportlab.lib.pagesizes")
        pdfcanvas = importlib.import_module("reportlab.pdfgen.canvas")
        A4 = pagesizes.A4
        Canvas = pdfcanvas.Canvas
        buf = BytesIO()
        c = Canvas(buf, pagesize=A4)
        c.setFont("Helvetica", 12)
        c.drawString(50, 800, f"Toplam Ciro: {total_revenue:.2f} ₺")
        c.drawString(50, 780, "Toplam Bahşiş: 0.00 ₺")
        c.drawString(50, 760, "En Çok Satanlar:")
        y = 740
        for row in top:
            c.drawString(60, y, f"{row['name']} - {row['qty']} adet - {row['total']:.2f} ₺")
            y -= 18
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 800
        c.showPage()
        c.setFont("Helvetica", 12)
        c.drawString(50, 800, "AI Analizi:")
        y = 780
        for line in analysis.split("\n"):
            c.drawString(60, y, line)
            y -= 18
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 800
        c.save()
        buf.seek(0)
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "static", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        path = os.path.join(uploads_dir, "closing_report.pdf")
        with open(path, "wb") as f:
            f.write(buf.read())
        return FileResponse(path, media_type="application/pdf", filename="closing_report.pdf")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail="PDF oluşturulamadı")

def generate_ai_insight(daily_data, stock_data):
    insights = []
    today_rev = daily_data.get('today_revenue', 0)
    avg_rev = daily_data.get('average_revenue', 0)
    if avg_rev:
        if today_rev > avg_rev * 1.2:
            pct = int(((today_rev-avg_rev)/avg_rev)*100)
            insights.append(f"Harika! Bugün ciro ortalamanın %{pct} üzerinde.")
        elif today_rev < avg_rev * 0.8:
            insights.append("Bugün ciro beklentinin altında. Kampanya yapmayı düşünebilirsiniz.")
    critical_items = [s for s in stock_data if s.get('track_stock') and s.get('stock', 0) <= 15]
    if critical_items:
        names = ", ".join([i['name'] for i in critical_items[:3]])
        insights.append(f"Stok Alarmı: {names} tükenmek üzere.")
    top_product = daily_data.get('top_product')
    if top_product:
        insights.append(f"Günün Yıldızı: '{top_product}' çok satıyor.")
    return insights

@router.get("/reports/daily-smart")
async def get_smart_daily_report(db: Session = Depends(get_session)):
    from datetime import date, datetime
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    orders = db.query(Order).filter(Order.created_at >= start).all()
    revenue = sum(float(o.total_amount or 0.0) for o in orders)
    movements = db.query(StockMovement).filter(StockMovement.created_at >= start).all()
    stock_in = sum(int(m.quantity or 0) for m in movements if int(m.quantity or 0) > 0)
    stock_out = sum(abs(int(m.quantity or 0)) for m in movements if int(m.quantity or 0) < 0)
    products = db.query(Product).filter(Product.track_stock == True).all()
    stock_status = [{"name": p.name, "stock": int(p.stock or 0), "track_stock": True} for p in products]
    data_for_ai = {
        "today_revenue": revenue,
        "average_revenue": 5000,
        "top_product": "Karışık Pizza"
    }
    ai_comments = generate_ai_insight(data_for_ai, stock_status)
    return {
        "date": today.isoformat(),
        "financials": {"revenue": revenue, "order_count": len(orders)},
        "inventory": {"items_in": stock_in, "items_sold": stock_out},
        "ai_analysis": ai_comments
    }

class InventoryUpdate(BaseModel):
    quantity: int

@router.get("/inventory")
async def list_inventory(
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    products = db.query(Product).filter(Product.is_active == True).all()
    inv_map = {i.product_id: i.quantity for i in db.query(Inventory).all()}
    return [{"product_id": p.id, "name": p.name, "quantity": int(inv_map.get(p.id, 0))} for p in products]

@router.put("/inventory/{product_id}")
async def update_inventory(
    product_id: int,
    data: InventoryUpdate,
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        inv = Inventory(product_id=product_id, quantity=int(data.quantity or 0))
        db.add(inv)
    else:
        inv.quantity = int(data.quantity or 0)
    db.commit()
    return {"product_id": product_id, "quantity": inv.quantity}

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
    
    if settings.logo_url is not None:
        config.logo_url = settings.logo_url
    
    db.commit()
    return {"message": "Ayarlar başarıyla güncellendi"}

@router.post("/settings/logo")
async def upload_restaurant_logo(
    file: UploadFile = File(...),
    current_user = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_session)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Sadece resim dosyası yüklenebilir.")
    
    # Exe uyumlu yol
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        UPLOAD_DIR = os.path.join(base_dir, "frontend", "static", "uploads")
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        UPLOAD_DIR = os.path.join(BASE_DIR, "frontend", "static", "uploads")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"restaurant_logo.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya kaydedilemedi: {str(e)}")
        
    logo_url = f"/static/uploads/{filename}"
    
    config = db.query(RestaurantConfig).first()
    if not config:
        config = RestaurantConfig()
        db.add(config)
    
    config.logo_url = logo_url
    db.commit()
    
    return {"logo_url": logo_url}
