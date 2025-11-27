from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User, Product, Category, Order, Table, OrderItem, OrderStatus, RestaurantConfig, StockMovement, Inventory, get_session
from services.ai_service import generate_analysis_text
from services.ai_service import generate_ai_answer
from collections import defaultdict
from io import BytesIO
from fastapi.responses import FileResponse
import importlib
from auth import require_role, get_current_active_user
from models import UserRole
from datetime import datetime, date, timedelta
from sqlalchemy import func, desc, String
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
        try:
            pdfmetrics = importlib.import_module("reportlab.pdfbase.pdfmetrics")
            ttfonts = importlib.import_module("reportlab.pdfbase.ttfonts")
            font_candidates = [
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "segoeui.ttf")
            ]
            font_path = next((p for p in font_candidates if os.path.exists(p)), None)
            if font_path:
                pdfmetrics.registerFont(ttfonts.TTFont("UIFont", font_path))
                c.setFont("UIFont", 12)
            else:
                c.setFont("Helvetica", 12)
        except Exception:
            c.setFont("Helvetica", 12)
        c.drawString(50, 800, f"Toplam Ciro: {total_revenue:.2f} ₺")
        
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
@router.get("/reports/full-pdf")
async def full_report_pdf(start_date: date = Query(None), end_date: date = Query(None), include_ai: bool = Query(True), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    s = datetime.combine(start_date, datetime.min.time())
    e = datetime.combine(end_date, datetime.max.time())
    orders = db.query(Order).filter(Order.created_at >= s, Order.created_at <= e).all()
    total_revenue = 0.0
    total_orders = 0
    cancelled_orders = 0
    for o in orders:
        st = (o.status.value if o.status else "").lower()
        total_orders += 1
        if st in ["cancelled", "iptal"]:
            cancelled_orders += 1
        else:
            total_revenue += float(o.total_amount or 0.0)
    products = db.query(Product).all()
    inv_map = {i.product_id: i.quantity for i in db.query(Inventory).all()}
    users = db.query(User).all()
    tables_total = db.query(Table).filter(Table.is_active == True).count()
    table_rows = db.query(Table).filter(Table.is_active == True).order_by(Table.number.asc()).all()
    items = db.query(OrderItem).join(Order, OrderItem.order_id == Order.id).filter(Order.created_at >= s, Order.created_at <= e).all()
    prod_counts = {}
    for it in items:
        pid = it.product_id
        if pid not in prod_counts:
            prod_counts[pid] = {"name": it.product.name if it.product else str(pid), "qty": 0, "total": 0.0}
        prod_counts[pid]["qty"] += int(it.quantity or 0)
        prod_counts[pid]["total"] += float(it.subtotal or 0.0)
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - (end_date - start_date)
    ps = datetime.combine(prev_start, datetime.min.time())
    pe = datetime.combine(prev_end, datetime.max.time())
    prev_orders = db.query(Order).filter(Order.created_at >= ps, Order.created_at <= pe).all()
    prev_rev = sum(float(o.total_amount or 0.0) for o in prev_orders if (o.status and o.status.value.lower() not in ["cancelled","iptal"]))
    try:
        pagesizes = importlib.import_module("reportlab.lib.pagesizes")
        pdfcanvas = importlib.import_module("reportlab.pdfgen.canvas")
        A4 = pagesizes.A4
        Canvas = pdfcanvas.Canvas
        buf = BytesIO()
        c = Canvas(buf, pagesize=A4)
        try:
            pdfmetrics = importlib.import_module("reportlab.pdfbase.pdfmetrics")
            ttfonts = importlib.import_module("reportlab.pdfbase.ttfonts")
            font_candidates = [
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "segoeui.ttf")
            ]
            font_path = next((p for p in font_candidates if os.path.exists(p)), None)
            if font_path:
                pdfmetrics.registerFont(ttfonts.TTFont("UIFont", font_path))
                c.setFont("UIFont", 14)
            else:
                c.setFont("Helvetica-Bold", 14)
        except Exception:
            c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 800, "Kapsamlı Yönetim Raporu")
        # İçindekiler
        toc = [
            "1. Genel Bakış",
            "2. Ürün Satışları",
            "3. Envanter",
            "4. Personel",
            "5. Masalar",
            "6. AI İçgörü (opsiyonel)"
        ]
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 730, "İçindekiler")
        c.setFont("Helvetica", 10)
        ytoc = 710
        for line in toc:
            c.drawString(60, ytoc, line)
            ytoc -= 16
        c.showPage()
        c.setFont("Helvetica", 10)
        c.drawString(50, 780, f"Aralık: {start_date.isoformat()} - {end_date.isoformat()}")
        c.drawString(50, 760, f"Toplam Ciro: {total_revenue:.2f} ₺ | Toplam Sipariş: {total_orders} | İptaller: {cancelled_orders}")
        c.drawString(50, 740, f"Önceki Aralık Cirosu: {prev_rev:.2f} ₺ | Fark: {(total_revenue - prev_rev):.2f} ₺")
        y = 720
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Ürün Satışları (Top 15)")
        y -= 20
        c.setFont("Helvetica", 10)
        top = sorted([{**v} for v in prod_counts.values()], key=lambda x: x["total"], reverse=True)[:15]
        for row in top:
            c.drawString(60, y, f"{row['name']} - {row['qty']} adet - {row['total']:.2f} ₺")
            y -= 16
            if y < 100:
                c.showPage(); c.setFont("Helvetica", 10); y = 800
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Envanter Durumu")
        y -= 20
        c.setFont("Helvetica", 10)
        for p in products[:20]:
            qty = int(inv_map.get(p.id, 0))
            c.drawString(60, y, f"{p.name} - Stok: {qty}")
            y -= 16
            if y < 100:
                c.showPage(); c.setFont("Helvetica", 10); y = 800
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Personel")
        y -= 20
        c.setFont("Helvetica", 10)
        for u in users[:25]:
            c.drawString(60, y, f"{u.username} ({u.role.value if u.role else ''})")
            y -= 16
            if y < 100:
                c.showPage(); c.setFont("Helvetica", 10); y = 800
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Masalar")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(60, y, f"Aktif Masa Sayısı: {tables_total}")
        y -= 20
        c.setFont("Helvetica", 10)
        for t in table_rows[:40]:
            c.drawString(60, y, f"masa - {t.number} — {t.name}")
            y -= 16
            if y < 100:
                c.showPage(); c.setFont("Helvetica", 10); y = 800
        y -= 10
        if include_ai:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "AI İçgörü ve Tahmin")
            y -= 20
            matrix = [{"name": x["name"], "volume": x["qty"], "profit_proxy": x["total"]} for x in top]
            insight = generate_analysis_text(matrix)
            c.setFont("Helvetica", 10)
            for line in insight.split("\n"):
                c.drawString(60, y, line)
                y -= 16
                if y < 100:
                    c.showPage(); c.setFont("Helvetica", 10); y = 800
        c.showPage(); c.setFont("Helvetica", 10)
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "static", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        fname = f"full_report_{start_date.isoformat()}_{end_date.isoformat()}.pdf"
        path = os.path.join(uploads_dir, fname)
        c.save(); buf.seek(0)
        with open(path, "wb") as f:
            f.write(buf.read())
        return FileResponse(path, media_type="application/pdf", filename=fname)
    except Exception as e:
        logger.error(f"Full PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail="PDF oluşturulamadı")
@router.get("/reports/archive")
async def reports_archive(current_user = Depends(require_role([UserRole.ADMIN]))):
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    files = []
    for name in os.listdir(uploads_dir):
        if name.lower().endswith(".pdf"):
            p = os.path.join(uploads_dir, name)
            t = os.path.getmtime(p)
            sz = os.path.getsize(p)
            ext = "pdf" if name.lower().endswith(".pdf") else "csv"
            files.append({"name": name, "url": f"/static/uploads/{name}", "type": ext, "size": sz, "modified": datetime.fromtimestamp(t).isoformat()})
    return {"files": sorted(files, key=lambda x: x["name"], reverse=True)}

@router.delete("/reports/archive/{filename}")
async def delete_report_file(filename: str, current_user = Depends(require_role([UserRole.ADMIN]))):
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "static", "uploads")
    path = os.path.join(uploads_dir, filename)
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Yalnızca PDF silinebilir")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
    os.remove(path)
    return {"message": "silindi", "name": filename}
@router.get("/reports/ai/query")
async def ai_query(q: str = Query(...), start_date: date = Query(None), end_date: date = Query(None), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    s = datetime.combine(start_date, datetime.min.time())
    e = datetime.combine(end_date, datetime.max.time())
    orders = db.query(Order).filter(Order.created_at >= s, Order.created_at <= e).all()
    total_revenue = sum(float(o.total_amount or 0.0) for o in orders if (o.status and o.status.value.lower() not in ["cancelled","iptal"]))
    total_orders = len(orders)
    cancels = sum(1 for o in orders if (o.status and o.status.value.lower() in ["cancelled","iptal"]))
    inv_map = {i.product_id: int(i.quantity or 0) for i in db.query(Inventory).all()}
    products = db.query(Product).all()
    stock = []
    for p in products:
        qty = int(inv_map.get(p.id, int(p.stock or 0))) if bool(p.track_stock or False) else None
        if qty is not None and qty < 0:
            qty = 0
        stock.append({"name": p.name, "qty": qty, "track": bool(p.track_stock or False)})
    ctx = {"start": start_date.isoformat(), "end": end_date.isoformat(), "total_revenue": total_revenue, "total_orders": total_orders, "cancelled_orders": cancels, "stock": stock}
    text = generate_ai_answer(q, ctx)
    return {"answer": text, "context": ctx}

@router.post("/reports/snapshot/run")
async def run_daily_snapshot(run_date: date = Query(None), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    d = run_date or date.today()
    start = datetime.combine(d, datetime.min.time())
    end = datetime.combine(d, datetime.max.time())
    orders = db.query(Order).filter(Order.created_at >= start, Order.created_at <= end).all()
    total_orders = len(orders)
    total_revenue = 0.0
    cancelled_orders = 0
    for o in orders:
        status = (o.status.value if o.status else "").lower()
        if status in ["cancelled", "iptal"]:
            cancelled_orders += 1
        else:
            total_revenue += float(o.total_amount or 0.0)
    avg_order = (total_revenue / (total_orders - cancelled_orders)) if (total_orders - cancelled_orders) > 0 else 0.0
    from models import DailySalesSummary, DailyProductSummary
    existing = db.query(DailySalesSummary).filter(DailySalesSummary.date == d).first()
    if not existing:
        existing = DailySalesSummary(date=d)
        db.add(existing)
    existing.total_orders = total_orders
    existing.total_revenue = total_revenue
    existing.cancelled_orders = cancelled_orders
    existing.avg_order = avg_order
    items = db.query(OrderItem).join(Order, OrderItem.order_id == Order.id).filter(Order.created_at >= start, Order.created_at <= end).all()
    agg = {}
    for it in items:
        pid = it.product_id
        if pid not in agg:
            agg[pid] = {"qty": 0, "rev": 0.0}
        agg[pid]["qty"] += int(it.quantity or 0)
        agg[pid]["rev"] += float(it.subtotal or 0.0)
    for pid, vals in agg.items():
        r = db.query(DailyProductSummary).filter(DailyProductSummary.date == d, DailyProductSummary.product_id == pid).first()
        if not r:
            r = DailyProductSummary(date=d, product_id=pid)
            db.add(r)
        r.qty = vals["qty"]
        r.revenue = vals["rev"]
    db.commit()
    return {"message": "snapshot ok", "date": d.isoformat(), "total_orders": total_orders}

@router.post("/reports/snapshot/backfill")
async def backfill_snapshot(start_date: date = Query(...), end_date: date = Query(...), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    delta = end_date - start_date
    done = 0
    for i in range(delta.days + 1):
        d = start_date + timedelta(days=i)
        await run_daily_snapshot(d, current_user, db)
        done += 1
    return {"message": "backfill ok", "days": done}

@router.get("/reports/overview")
async def reports_overview(start_date: date = Query(None), end_date: date = Query(None), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    from models import DailySalesSummary
    rows = db.query(DailySalesSummary).filter(DailySalesSummary.date >= start_date, DailySalesSummary.date <= end_date).order_by(DailySalesSummary.date.asc()).all()
    if rows:
        total_orders = sum(int(r.total_orders or 0) for r in rows)
        total_revenue = sum(float(r.total_revenue or 0.0) for r in rows)
        cancelled_orders = sum(int(r.cancelled_orders or 0) for r in rows)
        daily_trend = [{"date": r.date.isoformat(), "revenue": float(r.total_revenue or 0.0)} for r in rows]
        return {"total_orders": total_orders, "total_revenue": total_revenue, "cancelled_orders": cancelled_orders, "daily_trend": daily_trend, "avg_order": (total_revenue / max(1, (total_orders - cancelled_orders)))}
    s = datetime.combine(start_date, datetime.min.time())
    e = datetime.combine(end_date, datetime.max.time())
    orders = db.query(Order).filter(Order.created_at >= s, Order.created_at <= e).all()
    total_revenue = 0.0
    total_orders = 0
    cancelled_orders = 0
    daily_map = {}
    delta = end_date - start_date
    for i in range(delta.days + 1):
        d = (start_date + timedelta(days=i)).isoformat()
        daily_map[d] = 0.0
    for o in orders:
        od = (o.created_at.date() if isinstance(o.created_at, datetime) else safe_parse_date(o.created_at).date())
        status = (o.status.value if o.status else "").lower()
        total_orders += 1
        if status in ["cancelled", "iptal"]:
            cancelled_orders += 1
        else:
            total_revenue += float(o.total_amount or 0.0)
            ds = od.isoformat()
            if ds in daily_map:
                daily_map[ds] += float(o.total_amount or 0.0)
    daily_trend = [{"date": k, "revenue": v} for k, v in sorted(daily_map.items())]
    return {"total_orders": total_orders, "total_revenue": total_revenue, "cancelled_orders": cancelled_orders, "daily_trend": daily_trend, "avg_order": (total_revenue / max(1, (total_orders - cancelled_orders)))}

@router.get("/reports/proto")
async def reports_proto(start_date: date = Query(None), end_date: date = Query(None), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    overview = await reports_overview(start_date, end_date, current_user, db)
    products = await reports_products(start_date, end_date, 10, current_user, db)
    cancels = await reports_cancellations(start_date, end_date, current_user, db)
    settings = await get_system_settings(db)
    return {"overview": overview, "products": products, "cancellations": cancels, "settings": settings}

@router.get("/reports/products")
async def reports_products(start_date: date = Query(None), end_date: date = Query(None), limit: int = Query(10, ge=1, le=100), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    from models import DailyProductSummary, Product
    rows = db.query(DailyProductSummary).filter(DailyProductSummary.date >= start_date, DailyProductSummary.date <= end_date).all()
    if rows:
        agg = {}
        for r in rows:
            k = r.product_id
            if k not in agg:
                agg[k] = {"qty": 0, "revenue": 0.0}
            agg[k]["qty"] += int(r.qty or 0)
            agg[k]["revenue"] += float(r.revenue or 0.0)
        prods = db.query(Product).filter(Product.id.in_(list(agg.keys()))).all()
        name_map = {p.id: p.name for p in prods}
        arr = [{"product_id": pid, "name": name_map.get(pid, str(pid)), "qty": v["qty"], "total": v["revenue"]} for pid, v in agg.items()]
        arr = sorted(arr, key=lambda x: x["total"], reverse=True)[:limit]
        return {"items": arr}
    s = datetime.combine(start_date, datetime.min.time())
    e = datetime.combine(end_date, datetime.max.time())
    items = db.query(OrderItem).join(Order, OrderItem.order_id == Order.id).filter(Order.created_at >= s, Order.created_at <= e).all()
    agg = {}
    for it in items:
        pid = it.product_id
        if pid not in agg:
            agg[pid] = {"qty": 0, "revenue": 0.0, "name": it.product.name if it.product else str(pid)}
        agg[pid]["qty"] += int(it.quantity or 0)
        agg[pid]["revenue"] += float(it.subtotal or 0.0)
    arr = [{"product_id": pid, "name": v["name"], "qty": v["qty"], "total": v["revenue"]} for pid, v in agg.items()]
    arr = sorted(arr, key=lambda x: x["total"], reverse=True)[:limit]
    return {"items": arr}

@router.get("/reports/cancellations")
async def reports_cancellations(start_date: date = Query(None), end_date: date = Query(None), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    s = datetime.combine(start_date, datetime.min.time())
    e = datetime.combine(end_date, datetime.max.time())
    orders = db.query(Order).filter(Order.created_at >= s, Order.created_at <= e).all()
    cancels = []
    total_cancel_amount = 0.0
    for o in orders:
        status = (o.status.value if o.status else "").lower()
        if status in ["cancelled", "iptal"]:
            total_cancel_amount += float(o.total_amount or 0.0)
            cancels.append({"id": o.id, "table_id": o.table_id, "table_number": o.table.number if o.table else None, "table_name": o.table.name if o.table else "", "total": float(o.total_amount or 0.0), "created_at": o.created_at.isoformat()})
    return {"items": cancels, "total": total_cancel_amount}

@router.get("/reports/orders")
async def reports_orders(start_date: date = Query(None), end_date: date = Query(None), status_filter: Optional[str] = Query(None), table_id: Optional[int] = Query(None), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    s = datetime.combine(start_date, datetime.min.time())
    e = datetime.combine(end_date, datetime.max.time())
    q = db.query(Order).filter(Order.created_at >= s, Order.created_at <= e)
    if table_id: q = q.filter(Order.table_id == table_id)
    if status_filter:
        sf = status_filter.lower().strip()
        q = q.filter(func.lower(func.cast(Order.status, String)) == sf)
    orders = q.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for o in orders:
        result.append({"id": o.id, "table_id": o.table_id, "table_name": o.table.name if o.table else "", "status": o.status.value if o.status else None, "total_amount": float(o.total_amount or 0.0), "created_at": o.created_at.isoformat()})
    return {"items": result}

@router.get("/reports/export")
async def reports_export(format: str = Query("pdf"), start_date: date = Query(None), end_date: date = Query(None), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    s = datetime.combine(start_date, datetime.min.time())
    e = datetime.combine(end_date, datetime.max.time())
    orders = db.query(Order).filter(Order.created_at >= s, Order.created_at <= e).all()
    if format.lower() != "pdf":
        raise HTTPException(status_code=400, detail="Yalnızca PDF destekleniyor")
    return await closing_report_pdf(current_user, db)

@router.get("/reports/insights")
async def reports_insights(start_date: date = Query(None), end_date: date = Query(None), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not start_date: start_date = date.today() - timedelta(days=7)
    if not end_date: end_date = date.today()
    s = datetime.combine(start_date, datetime.min.time())
    e = datetime.combine(end_date, datetime.max.time())
    items = db.query(OrderItem).join(Order, OrderItem.order_id == Order.id).filter(Order.created_at >= s, Order.created_at <= e).all()
    counts = {}
    for it in items:
        pid = it.product_id
        if pid not in counts:
            counts[pid] = {"name": it.product.name if it.product else str(pid), "qty": 0, "total": 0.0}
        counts[pid]["qty"] += int(it.quantity or 0)
        counts[pid]["total"] += float(it.subtotal or 0.0)
    matrix = [{"name": v["name"], "volume": v["qty"], "profit_proxy": v["total"]} for _, v in counts.items()]
    text = generate_analysis_text(matrix)
    return {"analysis": text}

@router.get("/reports/stock-status")
async def stock_status(current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    products = db.query(Product).all()
    inv_map = {i.product_id: int(i.quantity or 0) for i in db.query(Inventory).all()}
    data = []
    for p in products:
        qty = int(inv_map.get(p.id, int(p.stock or 0))) if bool(p.track_stock or False) else None
        if qty is not None and qty < 0:
            qty = 0
        data.append({"product_id": p.id, "name": p.name, "track": bool(p.track_stock or False), "qty": qty})
    return {"items": data}

@router.post("/tables/normalize-names")
async def normalize_table_names(current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    tables = db.query(Table).all()
    changed = 0
    for t in tables:
        desired = f"masa - {t.number}"
        if t.name != desired:
            t.name = desired
            changed += 1
    db.commit()
    return {"updated": changed}

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
