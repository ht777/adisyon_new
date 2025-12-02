from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User, UserRole, get_session, Table, TableState, WaiterTableAssignment
from auth import require_role, get_password_hash, verify_password
import random

router = APIRouter(prefix="/waiters", tags=["Waiters"])

class WaiterCreate(BaseModel):
    full_name: str

class WaiterResponse(BaseModel):
    id: int
    username: str
    full_name: str | None
    class Config:
        from_attributes = True

class WaiterAssignTables(BaseModel):
    table_ids: list[int]

@router.get("")
async def list_waiters(current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    users = db.query(User).filter(User.role == UserRole.WAITER).all()
    return [{"id": u.id, "username": u.username, "full_name": getattr(u, "full_name", None)} for u in users]

@router.post("")
async def create_waiter(data: WaiterCreate, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    base = data.full_name.strip().lower().replace(" ", "-")
    uname = base
    i = 1
    while db.query(User).filter(User.username == uname).first() is not None:
        i += 1
        uname = f"{base}-{i}"
    pin = "".join([str(random.randint(0,9)) for _ in range(4)])
    while True:
        exists = False
        for w in db.query(User).filter(User.role == UserRole.WAITER).all():
            if verify_password(pin, w.password_hash):
                exists = True
                break
        if not exists:
            break
        pin = "".join([str(random.randint(0,9)) for _ in range(4)])
    u = User(username=uname, full_name=data.full_name, password_hash=get_password_hash(pin), role=UserRole.WAITER, is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "username": u.username, "full_name": u.full_name, "pin": pin}

@router.delete("/{waiter_id}")
async def delete_waiter(waiter_id: int, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    u = db.query(User).filter(User.id == waiter_id, User.role == UserRole.WAITER).first()
    if not u:
        raise HTTPException(status_code=404, detail="Waiter not found")
    db.query(WaiterTableAssignment).filter(WaiterTableAssignment.user_id == waiter_id).delete()
    db.delete(u)
    db.commit()
    return {"message": "deleted"}

@router.get("/{waiter_id}/tables")
async def get_waiter_tables(waiter_id: int, current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR])), db: Session = Depends(get_session)):
    assigns = db.query(WaiterTableAssignment).filter(WaiterTableAssignment.user_id == waiter_id).all()
    ids = [a.table_id for a in assigns]
    tables = db.query(Table).filter(Table.id.in_(ids)).order_by(Table.number.asc()).all()
    result = []
    for t in tables:
        ts = db.query(TableState).filter(TableState.table_id == t.id).first()
        occ = bool(ts.is_occupied) if ts else False
        result.append({"id": t.id, "number": t.number, "name": t.name, "is_occupied": occ})
    return result

@router.put("/{waiter_id}/tables")
async def set_waiter_tables(waiter_id: int, data: WaiterAssignTables, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    u = db.query(User).filter(User.id == waiter_id, User.role == UserRole.WAITER).first()
    if not u:
        raise HTTPException(status_code=404, detail="Waiter not found")
    db.query(WaiterTableAssignment).filter(WaiterTableAssignment.user_id == waiter_id).delete()
    for tid in data.table_ids:
        t = db.query(Table).filter(Table.id == tid).first()
        if t:
            db.add(WaiterTableAssignment(user_id=waiter_id, table_id=tid))
    db.commit()
    return {"message": "ok"}

@router.post("/{waiter_id}/reset-pin")
async def reset_pin(waiter_id: int, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    u = db.query(User).filter(User.id == waiter_id, User.role == UserRole.WAITER).first()
    if not u:
        raise HTTPException(status_code=404, detail="Waiter not found")
    import random
    new_pin = "".join([str(random.randint(0,9)) for _ in range(4)])
    # ensure uniqueness among current waiter hashes
    while True:
        exists = False
        for w in db.query(User).filter(User.role == UserRole.WAITER).all():
            if verify_password(new_pin, w.password_hash):
                exists = True
                break
        if not exists:
            break
        new_pin = "".join([str(random.randint(0,9)) for _ in range(4)])
    u.password_hash = get_password_hash(new_pin)
    db.commit()
    return {"pin": new_pin}

@router.get("/assigned-tables")
async def my_tables(current_user: User = Depends(require_role([UserRole.WAITER])), db: Session = Depends(get_session)):
    assigns = db.query(WaiterTableAssignment).filter(WaiterTableAssignment.user_id == current_user.id).all()
    ids = [a.table_id for a in assigns]
    tables = db.query(Table).filter(Table.id.in_(ids)).order_by(Table.number.asc()).all()
    result = []
    for t in tables:
        ts = db.query(TableState).filter(TableState.table_id == t.id).first()
        occ = bool(ts.is_occupied) if ts else False
        result.append({"id": t.id, "number": t.number, "name": t.name, "is_occupied": occ})
    return result

@router.get("/available-tables")
async def available_tables(db: Session = Depends(get_session)):
    tables = db.query(Table).filter(Table.is_active == True).order_by(Table.number.asc()).all()
    result = []
    for t in tables:
        ts = db.query(TableState).filter(TableState.table_id == t.id).first()
        occ = bool(ts.is_occupied) if ts else False
        if not occ:
            result.append({"id": t.id, "number": t.number, "name": t.name, "is_occupied": False})
    return result

@router.post("/auto-assign")
async def auto_assign(current_user: User = Depends(require_role([UserRole.WAITER])), db: Session = Depends(get_session)):
    # Tüm aktif masaları ata (dolu/boş fark etmez - garson tüm masalarını görebilmeli)
    tables = db.query(Table).filter(Table.is_active == True).order_by(Table.number.asc()).all()
    all_ids = [t.id for t in tables]
    
    db.query(WaiterTableAssignment).filter(WaiterTableAssignment.user_id == current_user.id).delete()
    for tid in all_ids:
        db.add(WaiterTableAssignment(user_id=current_user.id, table_id=tid))
    db.commit()
    return {"assigned": len(all_ids)}
