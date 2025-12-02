from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, Enum, ForeignKey, Table, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

# --- ENUM SINIFLARI ---
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    KITCHEN = "kitchen"
    WAITER = "waiter"
    SUPERVISOR = "supervisor"

class OrderStatus(str, enum.Enum):
    BEKLIYOR = "pending"
    HAZIRLANIYOR = "preparing"
    HAZIR = "ready"
    TESLIM_EDILDI = "delivered"
    IPTAL = "cancelled"

class MovementType(str, enum.Enum):
    GIRIS = "giris"
    SATIS = "satis"
    IPTAL = "iptal"
    ZAYI = "zayi"
    DUZELTME = "duzeltme"

# --- TABLO MODELLERİ ---
# DİKKAT: datetime.utcnow YERİNE datetime.now KULLANILDI

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.WAITER)
    is_active = Column(Boolean, default=True)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now) # Değişti

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=True)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now) # Değişti
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    stock = Column(Integer, default=0)
    track_stock = Column(Boolean, default=False)
    initial_stock = Column(Integer, default=0)  # Kritik stok hesabı için başlangıç stok miktarı
    category = relationship("Category", back_populates="products")
    extra_groups = relationship("ProductExtraGroup", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")

class ExtraGroup(Base):
    __tablename__ = "extra_groups"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    is_required = Column(Boolean, default=False)
    max_selections = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now) # Değişti
    items = relationship("ExtraItem", back_populates="group")
    products = relationship("ProductExtraGroup", back_populates="extra_group")

class ExtraItem(Base):
    __tablename__ = "extra_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Float, default=0.0)
    group_id = Column(Integer, ForeignKey("extra_groups.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now) # Değişti
    group = relationship("ExtraGroup", back_populates="items")

class ProductExtraGroup(Base):
    __tablename__ = "product_extra_groups"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    extra_group_id = Column(Integer, ForeignKey("extra_groups.id"))
    created_at = Column(DateTime, default=datetime.now) # Değişti
    product = relationship("Product", back_populates="extra_groups")
    extra_group = relationship("ExtraGroup", back_populates="products")

class Table(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    number = Column(Integer, unique=True, nullable=False)
    qr_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now) # Değişti
    orders = relationship("Order", back_populates="table")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey("tables.id"))
    waiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Siparişi alan garson
    status = Column(Enum(OrderStatus), default=OrderStatus.BEKLIYOR)
    customer_notes = Column(String, nullable=True)
    total_amount = Column(Float, default=0.0)
    payment_method = Column(String, nullable=True)  # "cash" veya "card"
    daily_order_number = Column(Integer, nullable=True)  # Günlük sipariş numarası (her gün 1'den başlar)
    created_at = Column(DateTime, default=datetime.now) # Değişti
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now) # Değişti
    table = relationship("Table", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    extras = Column(JSON, default={})
    subtotal = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now) # Değişti
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class RestaurantConfig(Base):
    __tablename__ = "restaurant_config"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    restaurant_name = Column(String, default="Restoran Sipariş Sistemi")
    currency = Column(String, default="TRY")
    tax_rate = Column(Float, default=10.0)
    service_charge = Column(Float, default=0.0)
    wifi_password = Column(String, nullable=True)
    order_timeout_minutes = Column(Integer, default=30)
    logo_url = Column(String, nullable=True)

class TableState(Base):
    __tablename__ = "table_state"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey("tables.id"), unique=True)
    is_occupied = Column(Boolean, default=False)
    merged_with_table_id = Column(Integer, nullable=True)

class UserStats(Base):
    __tablename__ = "user_stats"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    total_orders = Column(Integer, default=0)  # Toplam sipariş sayısı (puan)
    total_sales_score = Column(Float, default=0.0)  # Toplam satış tutarı
    total_tips_collected = Column(Float, default=0.0)  # Kullanılmıyor artık

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True)
    quantity = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    movement_type = Column(Enum(MovementType), default=MovementType.GIRIS)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    product = relationship("Product", back_populates="stock_movements")
class WaiterTableAssignment(Base):
    __tablename__ = "waiter_table_assignments"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), index=True)
    created_at = Column(DateTime, default=datetime.now)
class DailySalesSummary(Base):
    __tablename__ = "daily_sales_summary"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    cancelled_orders = Column(Integer, default=0)
    avg_order = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
class DailyProductSummary(Base):
    __tablename__ = "daily_product_summary"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    qty = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
# Database setup
def get_engine():
    return create_engine("sqlite:///./restaurant.db", connect_args={"check_same_thread": False})

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

def ensure_schema():
    engine = get_engine()
    try:
        with engine.connect() as conn:
            # Users tablosu için full_name alanı
            cols = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
            names = set([c[1] for c in cols])
            if "full_name" not in names:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN full_name TEXT")
            
            # Orders tablosu için payment_method alanı
            order_cols = conn.exec_driver_sql("PRAGMA table_info(orders)").fetchall()
            order_names = set([c[1] for c in order_cols])
            if "payment_method" not in order_names:
                conn.exec_driver_sql("ALTER TABLE orders ADD COLUMN payment_method TEXT")
            
            # Products tablosu için initial_stock alanı
            product_cols = conn.exec_driver_sql("PRAGMA table_info(products)").fetchall()
            product_names = set([c[1] for c in product_cols])
            if "initial_stock" not in product_names:
                conn.exec_driver_sql("ALTER TABLE products ADD COLUMN initial_stock INTEGER DEFAULT 0")
            
            # Orders tablosu için daily_order_number alanı
            if "daily_order_number" not in order_names:
                conn.exec_driver_sql("ALTER TABLE orders ADD COLUMN daily_order_number INTEGER")
            
            # Mevcut siparişlere daily_order_number ata (null olanlar için)
            try:
                conn.exec_driver_sql("""
                    UPDATE orders 
                    SET daily_order_number = (
                        SELECT COUNT(*) + 1 
                        FROM orders o2 
                        WHERE DATE(o2.created_at) = DATE(orders.created_at) 
                        AND o2.id < orders.id
                    )
                    WHERE daily_order_number IS NULL
                """)
            except Exception:
                pass
            
            # Orders tablosu için waiter_id alanı
            if "waiter_id" not in order_names:
                conn.exec_driver_sql("ALTER TABLE orders ADD COLUMN waiter_id INTEGER")
            
            # UserStats tablosu için total_orders alanı
            try:
                stats_cols = conn.exec_driver_sql("PRAGMA table_info(user_stats)").fetchall()
                stats_names = set([c[1] for c in stats_cols])
                if "total_orders" not in stats_names:
                    conn.exec_driver_sql("ALTER TABLE user_stats ADD COLUMN total_orders INTEGER DEFAULT 0")
            except Exception:
                pass
            
            conn.commit()
    except Exception:
        pass
