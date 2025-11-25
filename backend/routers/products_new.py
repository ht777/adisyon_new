from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Product, Category, ExtraGroup, ExtraItem, ProductExtraGroup, get_session
from auth import require_role, get_current_active_user
from models import UserRole, StockMovement, MovementType
import os
import sys
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/products", tags=["Products"])

# --- MODELLER ---

class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    order: int = 0

class CategoryResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str]
    order: int
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True

# 500 Hatasını çözen özet model
class CategorySummary(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    class Config: from_attributes = True

class ExtraItemCreate(BaseModel):
    name: str
    price: float = 0.0

class ExtraGroupCreate(BaseModel):
    name: str
    is_required: bool = False
    max_selections: int = 1
    items: List[ExtraItemCreate]

class ExtraGroupResponse(BaseModel):
    id: int
    name: str
    is_required: bool
    max_selections: int
    items: List[Dict[str, Any]]
    class Config: from_attributes = True

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    is_featured: bool = False
    is_active: bool = True
    stock: int = 0
    track_stock: bool = False

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    image_url: Optional[str]
    category: Optional[CategorySummary] = None
    is_featured: bool
    is_active: bool
    created_at: datetime
    stock: int
    track_stock: bool
    class Config: from_attributes = True

class ProductDetailResponse(ProductResponse):
    extra_groups: List[Dict[str, Any]]

# --- ENDPOINTLER ---

@router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing: raise HTTPException(status_code=400, detail="Bu kategori zaten var")
    new_category = Category(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(active_only: bool = Query(True), db: Session = Depends(get_session)):
    query = db.query(Category)
    if active_only: query = query.filter(Category.is_active == True)
    return query.order_by(Category.order, Category.name).all()

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_session)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category: raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    return category

@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, category_update: CategoryCreate, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category: raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    for key, value in category_update.dict().items(): setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category

@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category: raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    category.is_active = False
    db.commit()
    return {"message": "Kategori silindi"}

# Ekstra Grupları
@router.post("/extra-groups", response_model=ExtraGroupResponse)
async def create_extra_group(extra_group: ExtraGroupCreate, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    new_group = ExtraGroup(name=extra_group.name, is_required=extra_group.is_required, max_selections=extra_group.max_selections)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    for item in extra_group.items:
        db.add(ExtraItem(name=item.name, price=item.price, group_id=new_group.id))
    db.commit()
    return db.query(ExtraGroup).filter(ExtraGroup.id == new_group.id).first()

@router.get("/extra-groups", response_model=List[ExtraGroupResponse])
async def get_extra_groups(active_only: bool = Query(True), db: Session = Depends(get_session)):
    query = db.query(ExtraGroup)
    if active_only: query = query.filter(ExtraGroup.items.any(ExtraItem.is_active == True))
    return query.all()

# --- GERİ EKLENEN FONKSİYON ---
@router.get("/extra-groups/{group_id}", response_model=ExtraGroupResponse)
async def get_extra_group(group_id: int, db: Session = Depends(get_session)):
    group = db.query(ExtraGroup).filter(ExtraGroup.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Ekstra grubu bulunamadı")
    return group

# Ürünler
@router.post("", response_model=ProductResponse)
async def create_product(product: ProductCreate, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    if not db.query(Category).filter(Category.id == product.category_id).first(): raise HTTPException(status_code=404, detail="Kategori yok")
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("", response_model=List[ProductResponse])
async def get_products(skip: int = 0, limit: int = 100, category_id: Optional[int] = None, featured_only: bool = False, active_only: bool = True, db: Session = Depends(get_session)):
    query = db.query(Product)
    if category_id: query = query.filter(Product.category_id == category_id)
    if featured_only: query = query.filter(Product.is_featured == True)
    if active_only: query = query.filter(Product.is_active == True)
    products = query.offset(skip).limit(limit).all()
    result = []
    for p in products:
        category_data = {"id": p.category.id, "name": p.category.name, "icon": p.category.icon} if p.category else None
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "image_url": p.image_url,
            "category": category_data,
            "is_featured": p.is_featured,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "stock": int(p.stock or 0),
            "track_stock": bool(p.track_stock or False)
        })
    return result

@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(product_id: int, db: Session = Depends(get_session)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product: raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    extra_groups = []
    for peg in product.extra_groups:
        group_data = {
            "id": peg.extra_group.id, "name": peg.extra_group.name, "is_required": peg.extra_group.is_required, "max_selections": peg.extra_group.max_selections,
            "items": [{"id": i.id, "name": i.name, "price": i.price, "is_active": i.is_active} for i in peg.extra_group.items if i.is_active]
        }
        extra_groups.append(group_data)
    
    category_data = {"id": product.category.id, "name": product.category.name, "icon": product.category.icon} if product.category else None
    from sqlalchemy.orm import Session as _Session
    return {
        "id": product.id, "name": product.name, "description": product.description, "price": product.price, "image_url": product.image_url,
        "category": category_data, "is_featured": product.is_featured, "is_active": product.is_active, "created_at": product.created_at, "stock": int(product.stock or 0), "track_stock": bool(product.track_stock or False), "extra_groups": extra_groups
    }

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product_update: ProductCreate, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product: raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    old_stock = int(product.stock or 0)
    for key, value in product_update.dict().items(): setattr(product, key, value)
    new_stock_val = int(product.stock or 0)
    if bool(product.track_stock or False) and new_stock_val != old_stock:
        diff = new_stock_val - old_stock
        movement_type = MovementType.GIRIS if diff > 0 else MovementType.DUZELTME
        db.add(StockMovement(product_id=product.id, quantity=diff, movement_type=movement_type, description="Admin Manuel Güncelleme"))
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
async def delete_product(product_id: int, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product: raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    product.is_active = False
    db.commit()
    return {"message": "Ürün silindi"}

@router.post("/{product_id}/extra-groups/{group_id}")
async def assign_extra_group_to_product(product_id: int, group_id: int, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    existing = db.query(ProductExtraGroup).filter(ProductExtraGroup.product_id==product_id, ProductExtraGroup.extra_group_id==group_id).first()
    if existing: raise HTTPException(status_code=400, detail="Zaten atanmış")
    db.add(ProductExtraGroup(product_id=product_id, extra_group_id=group_id))
    db.commit()
    return {"message": "Atandı"}

# --- GERİ EKLENEN FONKSİYON ---
@router.delete("/{product_id}/extra-groups/{group_id}")
async def remove_extra_group_from_product(product_id: int, group_id: int, current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    assignment = db.query(ProductExtraGroup).filter(ProductExtraGroup.product_id==product_id, ProductExtraGroup.extra_group_id==group_id).first()
    if not assignment: raise HTTPException(status_code=404, detail="Atama bulunamadı")
    db.delete(assignment)
    db.commit()
    return {"message": "Silindi"}

@router.post("/{product_id}/image")
async def upload_product_image(product_id: int, file: UploadFile = File(...), current_user = Depends(require_role([UserRole.ADMIN])), db: Session = Depends(get_session)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product: raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024: raise HTTPException(status_code=400, detail="Dosya çok büyük (Max 5MB)")
    
    # Exe uyumlu yol
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
        uploads_dir = base_dir / "uploads"
    else:
        base_dir = Path(__file__).resolve().parents[2]
        uploads_dir = base_dir / "frontend" / "static" / "uploads"

    uploads_dir.mkdir(parents=True, exist_ok=True)
    filename = f"p_{product_id}_{int(datetime.now().timestamp())}_{file.filename.replace(' ', '_')}"
    
    with open(uploads_dir / filename, "wb") as f: f.write(content)
    
    image_url = f"/static/uploads/{filename}"
    product.image_url = image_url
    db.commit()
    return {"image_url": image_url}
