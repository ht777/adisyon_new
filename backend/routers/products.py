from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from typing import List, Optional, Dict, Any
from database import DatabaseManager
from models import Product
from routers.admin import get_current_admin
from pydantic import BaseModel

router = APIRouter()
db_manager = DatabaseManager()

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    discounted_price: Optional[float] = None
    category: str
    features: Optional[Dict[str, Any]] = {}
    image_url: Optional[str] = None
    stock: int = 0

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    discounted_price: Optional[float] = None
    category: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None

@router.get("/products")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    active_only: bool = Query(True)
):
    """Tüm ürünleri getir"""
    try:
        products = db_manager.get_products(skip=skip, limit=limit, category=category, active_only=active_only)
        return {"products": [{
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "discounted_price": p.discounted_price,
            "category": p.category,
            "features": p.features,
            "image_url": p.image_url,
            "stock": p.stock,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat()
        } for p in products]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ürünler getirilirken hata: {str(e)}")

@router.get("/products/{product_id}")
async def get_product(product_id: int):
    """Belirli bir ürünü getir"""
    product = db_manager.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "discounted_price": product.discounted_price,
        "category": product.category,
        "features": product.features,
        "image_url": product.image_url,
        "stock": product.stock,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat()
    }

@router.post("/products")
async def create_product(product: ProductCreate):
    """Yeni ürün oluştur"""
    try:
        if product.category:
            db_manager.create_category(product.category)
        product_data = product.dict()
        new_product = db_manager.create_product(product_data)
        return {
            "id": new_product.id,
            "name": new_product.name,
            "description": new_product.description,
            "price": new_product.price,
            "discounted_price": new_product.discounted_price,
            "category": new_product.category,
            "features": new_product.features,
            "image_url": new_product.image_url,
            "stock": new_product.stock,
            "is_active": new_product.is_active,
            "created_at": new_product.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ürün oluşturulurken hata: {str(e)}")

@router.put("/products/{product_id}")
async def update_product(product_id: int, product: ProductUpdate):
    """Ürünü güncelle"""
    existing_product = db_manager.get_product(product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    try:
        update_data = {k: v for k, v in product.dict().items() if v is not None}
        if update_data.get("category"):
            db_manager.create_category(update_data["category"])
        updated_product = db_manager.update_product(product_id, update_data)
        return {
            "id": updated_product.id,
            "name": updated_product.name,
            "description": updated_product.description,
            "price": updated_product.price,
            "discounted_price": updated_product.discounted_price,
            "category": updated_product.category,
            "features": updated_product.features,
            "image_url": updated_product.image_url,
            "stock": updated_product.stock,
            "is_active": updated_product.is_active,
            "created_at": updated_product.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ürün güncellenirken hata: {str(e)}")

@router.delete("/products/{product_id}")
async def delete_product(product_id: int):
    """Ürünü sil (soft delete)"""
    existing_product = db_manager.get_product(product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    try:
        success = db_manager.delete_product(product_id)
        if success:
            return {"message": "Ürün başarıyla silindi"}
        else:
            raise HTTPException(status_code=500, detail="Ürün silinemedi")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ürün silinirken hata: {str(e)}")

@router.get("/categories")
async def get_categories():
    """Tüm kategorileri getir"""
    try:
        names = db_manager.list_categories()
        if names:
            return {"categories": names}
        session = db_manager.session
        categories = session.query(Product.category).distinct().all()
        return {"categories": [cat[0] for cat in categories]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kategoriler getirilirken hata: {str(e)}")

@router.post("/categories")
async def create_category(name: str, username: str = Depends(get_current_admin)):
    try:
        cat = db_manager.create_category(name)
        return {"id": cat.id, "name": cat.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kategori oluşturulurken hata: {str(e)}")

@router.delete("/categories/{name}")
async def delete_category(name: str, username: str = Depends(get_current_admin)):
    try:
        ok = db_manager.delete_category(name)
        if not ok:
            raise HTTPException(status_code=404, detail="Kategori bulunamadı")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kategori silinirken hata: {str(e)}")

@router.put("/categories/{name}")
async def rename_category(name: str, new_name: str, username: str = Depends(get_current_admin)):
    try:
        ok = db_manager.rename_category(name, new_name)
        if not ok:
            raise HTTPException(status_code=404, detail="Kategori bulunamadı")
        return {"renamed": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kategori düzenlenirken hata: {str(e)}")

@router.post("/products/{product_id}/image")
async def upload_product_image(product_id: int, file: UploadFile = File(...), username: str = Depends(get_current_admin)):
    try:
        product = db_manager.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Ürün bulunamadı")
        import os
        from pathlib import Path
        uploads_dir = Path(__file__).resolve().parents[2] / "frontend" / "static" / "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        filename = f"product_{product_id}_{file.filename}"
        file_path = uploads_dir / filename
        content = await file.read()
        if len(content) > 500 * 1024:
            raise HTTPException(status_code=400, detail="Dosya boyutu 500KB'ı geçemez")
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Yalnızca JPG/PNG kabul edilir")
        with open(file_path, "wb") as f:
            f.write(content)
        image_url = f"/static/uploads/{filename}"
        db_manager.update_product(product_id, {"image_url": image_url})
        return {"image_url": image_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Görsel yüklenirken hata: {str(e)}")

# Feature management
class FeatureCreate(BaseModel):
    name: str
    description: Optional[str] = None
    order: int = 0
    group: Optional[str] = None
    is_active: bool = True

class FeatureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    group: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/features")
async def list_features(username: str = Depends(get_current_admin)):
    try:
        features = db_manager.list_features()
        return {"features": [{
            "id": f.id, "name": f.name, "description": f.description, "image_url": f.image_url,
            "order": f.order, "group": f.group, "is_active": f.is_active, "created_at": f.created_at.isoformat()
        } for f in features]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Özellikler getirilirken hata: {str(e)}")

@router.post("/features")
async def create_feature(feature: FeatureCreate, username: str = Depends(get_current_admin)):
    try:
        created = db_manager.create_feature(feature.dict())
        return {"id": created.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Özellik oluşturulurken hata: {str(e)}")

@router.put("/features/{feature_id}")
async def update_feature(feature_id: int, feature: FeatureUpdate, username: str = Depends(get_current_admin)):
    try:
        updated = db_manager.update_feature(feature_id, {k: v for k, v in feature.dict().items() if v is not None})
        if not updated:
            raise HTTPException(status_code=404, detail="Özellik bulunamadı")
        return {"updated": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Özellik güncellenirken hata: {str(e)}")

@router.delete("/features/{feature_id}")
async def delete_feature(feature_id: int, username: str = Depends(get_current_admin)):
    try:
        ok = db_manager.delete_feature(feature_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Özellik bulunamadı")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Özellik silinirken hata: {str(e)}")

@router.post("/features/{feature_id}/image")
async def upload_feature_image(feature_id: int, file: UploadFile = File(...), username: str = Depends(get_current_admin)):
    try:
        import os
        from pathlib import Path
        content = await file.read()
        if len(content) > 500 * 1024:
            raise HTTPException(status_code=400, detail="Dosya boyutu 500KB'ı geçemez")
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Yalnızca JPG/PNG kabul edilir")
        uploads_dir = Path(__file__).resolve().parents[2] / "frontend" / "static" / "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        filename = f"feature_{feature_id}_{file.filename}"
        file_path = uploads_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)
        image_url = f"/static/uploads/{filename}"
        updated = db_manager.update_feature(feature_id, {"image_url": image_url})
        if not updated:
            raise HTTPException(status_code=404, detail="Özellik bulunamadı")
        return {"image_url": image_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Özellik görseli yüklenirken hata: {str(e)}")