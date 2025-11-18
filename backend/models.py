from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, Enum, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

# DURUM KODLARI GÜNCELLENDİ (Türkçe karakter sorunu bitti)
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    KITCHEN = "kitchen"
    WAITER = "waiter"
    SUPERVISOR = "supervisor"

class OrderStatus(str, enum.Enum):
    BEKLIYOR = "pending"       # Eski: bekliyor
    HAZIRLANIYOR = "preparing" # Eski: hazırlanıyor (sorunlu)
    HAZIR = "ready"            # Eski: hazır
    TESLIM_EDILDI = "delivered"
    IPTAL = "cancelled"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.WAITER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=True)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    category = relationship("Category", back_populates="products")
    extra_groups = relationship("ProductExtraGroup", back_populates="product")

class ExtraGroup(Base):
    __tablename__ = "extra_groups"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    is_required = Column(Boolean, default=False)
    max_selections = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("ExtraItem", back_populates="group")
    products = relationship("ProductExtraGroup", back_populates="extra_group")

class ExtraItem(Base):
    __tablename__ = "extra_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Float, default=0.0)
    group_id = Column(Integer, ForeignKey("extra_groups.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("ExtraGroup", back_populates="items")

class ProductExtraGroup(Base):
    __tablename__ = "product_extra_groups"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    extra_group_id = Column(Integer, ForeignKey("extra_groups.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="extra_groups")
    extra_group = relationship("ExtraGroup", back_populates="products")

class Table(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    number = Column(Integer, unique=True, nullable=False)
    qr_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    orders = relationship("Order", back_populates="table")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey("tables.id"))
    status = Column(Enum(OrderStatus), default=OrderStatus.BEKLIYOR)
    customer_notes = Column(String, nullable=True)
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class AdminSettings(Base):
    __tablename__ = "admin_settings"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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