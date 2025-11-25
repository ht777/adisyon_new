from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Table, get_session, Order, OrderStatus, TableState
from auth import require_role, get_current_active_user
from models import UserRole
from websocket_utils import broadcast_to_admin 
import qrcode
import io
import base64
import socket
from datetime import datetime

router = APIRouter(prefix="/tables", tags=["Tables"])

# --- MODELLER ---
class TableCreate(BaseModel):
    name: str
    number: int

class TableResponse(BaseModel):
    id: int
    name: str
    number: int
    qr_url: Optional[str]
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True

class TableUpdate(BaseModel):
    name: Optional[str] = None
    number: Optional[int] = None
    is_active: Optional[bool] = None

class WaiterCallRequest(BaseModel):
    type: str = "garson"  # "garson" veya "hesap"

# --- YARDIMCI FONKSİYONLAR ---
def get_base_url():
    """Bilgisayarın yerel IP adresini bulur"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Google DNS'e bağlanmayı dene (veri göndermez)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    return f"http://{local_ip}:8000"

async def generate_table_qr(table_number: int) -> str:
    """Masa için QR kod oluşturur"""
    base_url = get_base_url()
    # Müşteriyi direkt menüye ve o masaya yönlendir
    qr_data = f"{base_url}/menu?table={table_number}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

# --- ENDPOINTLER ---

@router.post("", response_model=TableResponse)
async def create_table(table: TableCreate, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if db.query(Table).filter(Table.number == table.number).first():
        raise HTTPException(status_code=400, detail="Bu masa numarası zaten var")
    
    new_table = Table(name=table.name, number=table.number)
    db.add(new_table)
    db.commit()
    db.refresh(new_table)
    
    # QR kod oluştur ve kaydet
    try:
        new_table.qr_url = await generate_table_qr(new_table.number)
        db.commit()
    except Exception as e:
        print(f"QR kod oluşturma hatası: {e}")
        # QR hatası olsa bile masayı oluştur, sonra tekrar denenebilir
    
    return new_table

@router.get("", response_model=List[TableResponse])
async def get_tables(skip: int=0, limit: int=100, active_only: bool=True, db: Session = Depends(get_session)):
    q = db.query(Table)
    if active_only:
        q = q.filter(Table.is_active == True)
    return q.order_by(Table.number).offset(skip).limit(limit).all()

@router.get("/{table_id}", response_model=TableResponse)
async def get_table(table_id: int, db: Session = Depends(get_session)):
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı")
    return table

@router.put("/{table_id}", response_model=TableResponse)
async def update_table(table_id: int, table_update: TableUpdate, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı")
    
    if table_update.number is not None and table_update.number != table.number:
        existing = db.query(Table).filter(
            Table.number == table_update.number,
            Table.id != table_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu masa numarası zaten kullanımda")
    
    # Güncelleme işlemi
    for key, value in table_update.dict(exclude_unset=True).items():
        setattr(table, key, value)
    
    # Numara değiştiyse QR kodu güncelle
    if table_update.number is not None:
        table.qr_url = await generate_table_qr(table.number)
    
    db.commit()
    db.refresh(table)
    return table

@router.delete("/{table_id}")
async def delete_table(table_id: int, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Masa bulunamadı")
    
    # Soft delete (pasife çekme)
    table.is_active = False
    db.commit()
    return {"message": "Masa başarıyla silindi"}

@router.get("/{table_id}/qr")
async def get_table_qr(table_id: int, db: Session = Depends(get_session)):
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    
    # QR kodu her zaman güncel IP ile yenile (IP değişmiş olabilir)
    table.qr_url = await generate_table_qr(table.number)
    db.commit()
    
    return {
        "table_name": table.name,
        "table_number": table.number,
        "qr_url": table.qr_url,
        "menu_url": f"{get_base_url()}/menu?table={table.number}"
    }

@router.post("/{table_id}/regenerate-qr")
async def regenerate_table_qr(table_id: int, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Bulunamadı")
        
    table.qr_url = await generate_table_qr(table.number)
    db.commit()
    return {
        "message": "Yenilendi",
        "qr_url": table.qr_url,
        "menu_url": f"{get_base_url()}/menu?table={table.number}"
    }

@router.post("/bulk-create")
async def create_tables_bulk(tables: List[TableCreate], current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    created = []
    for t in tables:
        if db.query(Table).filter(Table.number == t.number).first():
            continue
            
        nt = Table(name=t.name, number=t.number)
        db.add(nt)
        db.commit()
        db.refresh(nt)
        
        nt.qr_url = await generate_table_qr(nt.number)
        db.commit()
        created.append(nt)
        
    return {"message": f"{len(created)} masa oluşturuldu", "tables": created}

@router.get("/stats/summary")
async def get_tables_summary(
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])),
    db: Session = Depends(get_session)
):
    total_tables = db.query(Table).filter(Table.is_active == True).count()
    
    # Son 2 saatteki aktif siparişleri kontrol et
    from datetime import datetime, timedelta
    recent_time = datetime.now() - timedelta(hours=2)
    
    active_tables = db.query(Table).join(Order).filter(
        Table.is_active == True,
        Order.created_at >= recent_time,
        ~Order.status.in_(["delivered", "cancelled"]) # ~ işareti NOT anlamına gelir
    ).distinct().count()
    
    return {
        "total_tables": total_tables,
        "active_tables": active_tables,
        "available_tables": max(0, total_tables - active_tables)
    }

# --- GARSON VE HESAP ÇAĞIRMA ---
@router.post("/{table_id}/call-waiter")
async def call_waiter(
    table_id: int, 
    request: WaiterCallRequest = WaiterCallRequest(), # Varsayılan değer eklendi
    db: Session = Depends(get_session)
):
    """Müşteri butona bastığında burası çalışır"""
    # ID veya Masa Numarasına göre bul
    table = db.query(Table).filter((Table.id == table_id) | (Table.number == table_id)).first()
    
    if table:
        # Mesaj tipine göre içerik belirle
        msg_text = f"🛎️ {table.name} garson çağırıyor!"
        msg_type = "waiter_call"
        
        if request.type == "hesap":
            msg_text = f"💳 {table.name} HESAP İSTİYOR!"
            msg_type = "bill_request"
        
        # Admin paneline WebSocket ile bildir
        await broadcast_to_admin({
            "type": msg_type,
            "table_name": table.name,
            "message": msg_text,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        return {"message": "Bildirim başarıyla gönderildi"}
    
    raise HTTPException(status_code=404, detail="Masa bulunamadı")

@router.post("/transfer/{source_id}/{target_id}")
async def transfer_table_orders(source_id: int, target_id: int, db: Session = Depends(get_session)):
    source = db.query(Table).filter(Table.id == source_id).first()
    target = db.query(Table).filter(Table.id == target_id).first()
    if not source or not target:
        raise HTTPException(status_code=404, detail="Masa bulunamadı")
    active_orders = db.query(Order).filter(
        Order.table_id == source_id,
        Order.status.in_([OrderStatus.BEKLIYOR, OrderStatus.HAZIRLANIYOR])
    ).all()
    for o in active_orders:
        o.table_id = target_id
    db.commit()
    s = db.query(TableState).filter(TableState.table_id == source_id).first()
    if not s:
        s = TableState(table_id=source_id, is_occupied=False)
        db.add(s)
    else:
        s.is_occupied = False
    t = db.query(TableState).filter(TableState.table_id == target_id).first()
    if not t:
        t = TableState(table_id=target_id, is_occupied=True)
        db.add(t)
    else:
        t.is_occupied = True
    db.commit()
    return {"moved_orders": len(active_orders), "source_is_occupied": False, "target_is_occupied": True}

@router.post("/merge/{source_id}/{target_id}")
async def merge_tables(source_id: int, target_id: int, db: Session = Depends(get_session)):
    source = db.query(Table).filter(Table.id == source_id).first()
    target = db.query(Table).filter(Table.id == target_id).first()
    if not source or not target:
        raise HTTPException(status_code=404, detail="Masa bulunamadı")
    s = db.query(TableState).filter(TableState.table_id == source_id).first()
    if not s:
        s = TableState(table_id=source_id, merged_with_table_id=target_id)
        db.add(s)
    else:
        s.merged_with_table_id = target_id
    t = db.query(TableState).filter(TableState.table_id == target_id).first()
    if not t:
        t = TableState(table_id=target_id, is_occupied=True)
        db.add(t)
    else:
        t.is_occupied = True
    db.commit()
    return {"message": "Birleştirildi", "source_merged_with": target_id}
