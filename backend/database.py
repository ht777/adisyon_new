from sqlalchemy.orm import Session
from models import Product, Order, OrderStatus, Category, AdminSettings, Feature, QrCode, ArchivedOrder, get_session
from typing import List, Optional, Dict, Any
import json
import hashlib

class DatabaseManager:
    def __init__(self):
        self.session = get_session()
    
    def get_products(self, skip: int = 0, limit: int = 100, category: Optional[str] = None, 
                    features: Optional[Dict] = None, active_only: bool = True) -> List[Product]:
        query = self.session.query(Product)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        if category:
            query = query.filter(Product.category == category)
        
        if features:
            for key, value in features.items():
                query = query.filter(Product.features[key].astext == str(value))
        
        return query.offset(skip).limit(limit).all()
    
    def get_product(self, product_id: int) -> Optional[Product]:
        return self.session.query(Product).filter(Product.id == product_id).first()
    
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        product = Product(**product_data)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product
    
    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Product]:
        product = self.get_product(product_id)
        if product:
            for key, value in product_data.items():
                setattr(product, key, value)
            self.session.commit()
            self.session.refresh(product)
        return product
    
    def delete_product(self, product_id: int) -> bool:
        product = self.get_product(product_id)
        if product:
            product.is_active = False
            self.session.commit()
            return True
        return False
    
    def check_stock(self, product_id: int, quantity: int) -> bool:
        product = self.get_product(product_id)
        return product and product.stock >= quantity if product else False
    
    def update_stock(self, product_id: int, quantity: int) -> bool:
        product = self.get_product(product_id)
        if product and product.stock >= quantity:
            product.stock -= quantity
            self.session.commit()
            return True
        return False
    
    def create_order(self, order_data: Dict[str, Any]) -> Order:
        # Check stock for all items
        for item in order_data['items']:
            if not self.check_stock(item['product_id'], item['quantity']):
                raise ValueError(f"Yetersiz stok: Ürün ID {item['product_id']}")
        
        # Create order
        order = Order(**order_data)
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        
        # Update stock
        for item in order_data['items']:
            self.update_stock(item['product_id'], item['quantity'])
        
        return order
    
    def get_orders(self, skip: int = 0, limit: int = 100, status: Optional[str] = None,
                   table_number: Optional[int] = None) -> List[Order]:
        query = self.session.query(Order)
        
        if status:
            query = query.filter(Order.status == status)
        
        if table_number:
            query = query.filter(Order.table_number == table_number)
        
        return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_order(self, order_id: int) -> Optional[Order]:
        return self.session.query(Order).filter(Order.id == order_id).first()
    
    def update_order_status(self, order_id: int, status: str) -> Optional[Order]:
        order = self.get_order(order_id)
        if order:
            order.status = status
            self.session.commit()
            self.session.refresh(order)
        return order
    
    def get_order_stats(self) -> Dict[str, Any]:
        total_orders = self.session.query(Order).count()
        pending_orders = self.session.query(Order).filter(Order.status == OrderStatus.BEKLIYOR).count()
        preparing_orders = self.session.query(Order).filter(Order.status == OrderStatus.HAZIRLANIYOR).count()
        ready_orders = self.session.query(Order).filter(Order.status == OrderStatus.HAZIR).count()
        cancelled_orders = self.session.query(Order).filter(Order.status == OrderStatus.IPTAL).count()
        
        return {
            "total": total_orders,
            "pending": pending_orders,
            "preparing": preparing_orders,
            "ready": ready_orders,
            "cancelled": cancelled_orders
        }

    def close(self):
        self.session.close()

    # Category management
    def list_categories(self) -> List[str]:
        categories = self.session.query(Category).all()
        return [c.name for c in categories]

    def create_category(self, name: str) -> Category:
        existing = self.session.query(Category).filter(Category.name == name).first()
        if existing:
            return existing
        category = Category(name=name)
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category

    def delete_category(self, name: str) -> bool:
        cat = self.session.query(Category).filter(Category.name == name).first()
        if not cat:
            return False
        self.session.delete(cat)
        self.session.commit()
        return True

    def rename_category(self, old_name: str, new_name: str) -> bool:
        cat = self.session.query(Category).filter(Category.name == old_name).first()
        if not cat:
            return False
        cat.name = new_name
        # Update products referencing the old category name
        self.session.query(Product).filter(Product.category == old_name).update({Product.category: new_name})
        self.session.commit()
        return True

    # Admin settings
    def get_admin_credentials(self) -> Optional[Dict[str, str]]:
        settings = self.session.query(AdminSettings).order_by(AdminSettings.id.asc()).first()
        if not settings:
            return None
        return {"username": settings.username, "password_hash": settings.password_hash}

    def set_admin_credentials(self, username: str, password: str) -> AdminSettings:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        settings = self.session.query(AdminSettings).order_by(AdminSettings.id.asc()).first()
        if settings:
            settings.username = username
            settings.password_hash = password_hash
            self.session.commit()
            self.session.refresh(settings)
            return settings
        new_settings = AdminSettings(username=username, password_hash=password_hash)
        self.session.add(new_settings)
        self.session.commit()
        self.session.refresh(new_settings)
        return new_settings

    # Feature management
    def list_features(self) -> List[Feature]:
        return self.session.query(Feature).order_by(Feature.group.asc().nullsfirst(), Feature.order.asc(), Feature.name.asc()).all()

    def create_feature(self, data: Dict[str, Any]) -> Feature:
        feature = Feature(**data)
        self.session.add(feature)
        self.session.commit()
        self.session.refresh(feature)
        return feature

    def update_feature(self, feature_id: int, data: Dict[str, Any]) -> Optional[Feature]:
        feature = self.session.query(Feature).filter(Feature.id == feature_id).first()
        if not feature:
            return None
        for k, v in data.items():
            setattr(feature, k, v)
        self.session.commit()
        self.session.refresh(feature)
        return feature

    def delete_feature(self, feature_id: int) -> bool:
        feature = self.session.query(Feature).filter(Feature.id == feature_id).first()
        if not feature:
            return False
        self.session.delete(feature)
        self.session.commit()
        return True

    # QR code management
    def list_qrcodes(self) -> List[QrCode]:
        return self.session.query(QrCode).order_by(QrCode.created_at.desc()).all()

    def create_qrcode(self, table_number: int, label: Optional[str] = None) -> QrCode:
        qr = QrCode(table_number=table_number, label=label)
        self.session.add(qr)
        self.session.commit()
        self.session.refresh(qr)
        return qr

    def update_qrcode(self, qr_id: int, table_number: Optional[int] = None, label: Optional[str] = None) -> Optional[QrCode]:
        qr = self.session.query(QrCode).filter(QrCode.id == qr_id).first()
        if not qr:
            return None
        if table_number is not None:
            qr.table_number = table_number
        if label is not None:
            qr.label = label
        self.session.commit()
        self.session.refresh(qr)
        return qr

    def delete_qrcode(self, qr_id: int) -> bool:
        qr = self.session.query(QrCode).filter(QrCode.id == qr_id).first()
        if not qr:
            return False
        self.session.delete(qr)
        self.session.commit()
        return True

    # Order archive and reset
    def archive_all_orders(self) -> int:
        orders = self.session.query(Order).all()
        count = 0
        for o in orders:
            archived = ArchivedOrder(
                original_order_id=o.id,
                table_number=o.table_number,
                items=o.items,
                status=o.status if isinstance(o.status, str) else getattr(o.status, 'value', str(o.status)),
                customer_notes=o.customer_notes,
                is_urgent=o.is_urgent,
                created_at=o.created_at
            )
            self.session.add(archived)
            self.session.delete(o)
            count += 1
        self.session.commit()
        return count

    def list_archived_orders(self, skip: int = 0, limit: int = 100, table_number: Optional[int] = None) -> List[ArchivedOrder]:
        query = self.session.query(ArchivedOrder)
        if table_number:
            query = query.filter(ArchivedOrder.table_number == table_number)
        return query.order_by(ArchivedOrder.archived_at.desc()).offset(skip).limit(limit).all()

    def report_orders(self) -> Dict[str, Any]:
        stats = self.get_order_stats()
        by_table = self.session.query(Order.table_number).all()
        table_counts: Dict[int, int] = {}
        for t in by_table:
            table_counts[t[0]] = table_counts.get(t[0], 0) + 1
        return {"stats": stats, "by_table": table_counts}