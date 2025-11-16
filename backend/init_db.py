#!/usr/bin/env python3
"""
Database initialization and migration script for Restaurant Ordering System
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from models import create_tables, get_session, User, UserRole, Category, Product, ExtraGroup, ExtraItem, Table
from auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_admin():
    """Create default admin user"""
    try:
        db = next(get_session())
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            logger.info("Default admin user already exists")
            return
        
        # Create default admin
        admin_user = User(
            username="admin",
            email="admin@restaurant.com",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        logger.info("Default admin user created successfully")
        logger.info("Username: admin")
        logger.info("Password: admin123")
        logger.info("⚠️  IMPORTANT: Change the default password immediately!")
        
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_categories():
    """Create sample categories"""
    try:
        db = next(get_session())
        
        # Check if categories already exist
        existing_categories = db.query(Category).count()
        if existing_categories > 0:
            logger.info(f"{existing_categories} categories already exist")
            return
        
        sample_categories = [
            {"name": "Ana Yemekler", "description": "Lezzetli ana yemeklerimiz"},
            {"name": "Başlangıçlar", "description": "Neşeli başlangıçlar"},
            {"name": "Salatalar", "description": "Taze ve sağlıklı salatalar"},
            {"name": "İçecekler", "description": "Soğuk ve sıcak içecekler"},
            {"name": "Tatlılar", "description": "Tatlı final"},
            {"name": "Pizzalar", "description": "İtalyan pizzaları"},
            {"name": "Burgerler", "description": "Özel burgerler"},
            {"name": "Deniz Ürünleri", "description": "Taze deniz ürünleri"}
        ]
        
        for cat_data in sample_categories:
            category = Category(**cat_data)
            db.add(category)
        
        db.commit()
        logger.info(f"Created {len(sample_categories)} sample categories")
        
    except Exception as e:
        logger.error(f"Error creating sample categories: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_products():
    """Create sample products"""
    try:
        db = next(get_session())
        
        # Check if products already exist
        existing_products = db.query(Product).count()
        if existing_products > 0:
            logger.info(f"{existing_products} products already exist")
            return
        
        # Get categories
        main_dishes = db.query(Category).filter(Category.name == "Ana Yemekler").first()
        starters = db.query(Category).filter(Category.name == "Başlangıçlar").first()
        drinks = db.query(Category).filter(Category.name == "İçecekler").first()
        desserts = db.query(Category).filter(Category.name == "Tatlılar").first()
        pizzas = db.query(Category).filter(Category.name == "Pizzalar").first()
        burgers = db.query(Category).filter(Category.name == "Burgerler").first()
        
        sample_products = [
            # Ana Yemekler
            {"name": "Izgara Köfte", "description": "Özel baharatlarla hazırlanmış köfte", "price": 85.00, "category_id": main_dishes.id if main_dishes else None},
            {"name": "Tavuk Şiş", "description": "Izgara tavuk şiş", "price": 75.00, "category_id": main_dishes.id if main_dishes else None},
            {"name": "Kuzu Pirzola", "description": "Izgara kuzu pirzola", "price": 120.00, "category_id": main_dishes.id if main_dishes else None},
            {"name": "Balık Tava", "description": "Taze balık tava", "price": 95.00, "category_id": main_dishes.id if main_dishes else None},
            
            # Başlangıçlar
            {"name": "Çoban Salata", "description": "Taze sebzelerle hazırlanmış salata", "price": 35.00, "category_id": starters.id if starters else None},
            {"name": "Humus", "description": "Orta Doğu usulü humus", "price": 30.00, "category_id": starters.id if starters else None},
            {"name": "Atom", "description": "Yoğurtlu atom", "price": 25.00, "category_id": starters.id if starters else None},
            
            # İçecekler
            {"name": "Kola", "description": "Soğuk kola", "price": 15.00, "category_id": drinks.id if drinks else None},
            {"name": "Ayran", "description": "Taze ayran", "price": 10.00, "category_id": drinks.id if drinks else None},
            {"name": "Çay", "description": "Sıcak çay", "price": 5.00, "category_id": drinks.id if drinks else None},
            {"name": "Türk Kahvesi", "description": "Geleneksel Türk kahvesi", "price": 20.00, "category_id": drinks.id if drinks else None},
            
            # Tatlılar
            {"name": "Baklava", "description": "Antep baklavası", "price": 45.00, "category_id": desserts.id if desserts else None},
            {"name": "Künefe", "description": "Sıcak künefe", "price": 40.00, "category_id": desserts.id if desserts else None},
            {"name": "Sütlaç", "description": "Fırın sütlaç", "price": 25.00, "category_id": desserts.id if desserts else None},
            
            # Pizzalar
            {"name": "Margherita Pizza", "description": "Klasik margherita", "price": 65.00, "category_id": pizzas.id if pizzas else None},
            {"name": "Pepperoni Pizza", "description": "Pepperonili pizza", "price": 75.00, "category_id": pizzas.id if pizzas else None},
            
            # Burgerler
            {"name": "Cheeseburger", "description": "Özel soslu cheeseburger", "price": 55.00, "category_id": burgers.id if burgers else None},
            {"name": "Chicken Burger", "description": "Tavuk burger", "price": 50.00, "category_id": burgers.id if burgers else None},
        ]
        
        for product_data in sample_products:
            product = Product(**product_data)
            db.add(product)
        
        db.commit()
        logger.info(f"Created {len(sample_products)} sample products")
        
    except Exception as e:
        logger.error(f"Error creating sample products: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_extras():
    """Create sample extras with groups"""
    try:
        db = next(get_session())
        
        # Check if extras already exist
        existing_groups = db.query(ExtraGroup).count()
        if existing_groups > 0:
            logger.info(f"{existing_groups} extra groups already exist")
            return
        
        # Create extra groups
        sos_group = ExtraGroup(
            name="Ekstra Soslar",
            is_required=False,
            max_selections=3
        )
        db.add(sos_group)
        
        yan_urun_group = ExtraGroup(
            name="Yan Ürünler",
            is_required=False,
            max_selections=2
        )
        db.add(yan_urun_group)
        
        db.flush()  # Get IDs for groups
        
        # Create extra items for sos group
        sos_items = [
            {"name": "Ranch Sos", "price": 7.00, "group_id": sos_group.id},
            {"name": "Barbekü Sos", "price": 7.00, "group_id": sos_group.id},
            {"name": "Acı Sos", "price": 5.00, "group_id": sos_group.id},
            {"name": "Mayonez", "price": 5.00, "group_id": sos_group.id},
            {"name": "Ketçap", "price": 3.00, "group_id": sos_group.id}
        ]
        
        for sos_data in sos_items:
            sos_item = ExtraItem(**sos_data)
            db.add(sos_item)
        
        # Create extra items for yan ürün group
        yan_urun_items = [
            {"name": "Patates Kızartması", "price": 15.00, "group_id": yan_urun_group.id},
            {"name": "Soğan Halkaları", "price": 20.00, "group_id": yan_urun_group.id},
            {"name": "Ekstra Ekmek", "price": 3.00, "group_id": yan_urun_group.id},
            {"name": "Yeşillik", "price": 5.00, "group_id": yan_urun_group.id}
        ]
        
        for yan_data in yan_urun_items:
            yan_item = ExtraItem(**yan_data)
            db.add(yan_item)
        
        db.commit()
        logger.info(f"Created extra groups and items successfully")
        
    except Exception as e:
        logger.error(f"Error creating sample extras: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_tables():
    """Create sample tables"""
    try:
        db = next(get_session())
        
        # Check if tables already exist
        existing_tables = db.query(Table).count()
        if existing_tables > 0:
            logger.info(f"{existing_tables} tables already exist")
            return
        
        sample_tables = []
        for i in range(1, 21):  # Create 20 tables
            table = Table(
                name=f"Masa {i}",
                number=i,
                capacity=4 if i <= 15 else 6,  # First 15 tables for 4 people, rest for 6
                is_active=True,
                qr_url=None  # This will be generated properly by the API
            )
            sample_tables.append(table)
            db.add(table)
        
        db.commit()
        logger.info(f"Created {len(sample_tables)} sample tables")
        
    except Exception as e:
        logger.error(f"Error creating sample tables: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    logger.info("Starting Restaurant Ordering System database initialization...")
    
    try:
        # Create database tables
        logger.info("Creating database tables...")
        create_tables()
        
        # Create default admin user
        logger.info("Creating default admin user...")
        create_default_admin()
        
        # Create sample data
        logger.info("Creating sample categories...")
        create_sample_categories()
        
        logger.info("Creating sample products...")
        create_sample_products()
        
        logger.info("Creating sample extras...")
        create_sample_extras()
        
        logger.info("Creating sample tables...")
        create_sample_tables()
        
        logger.info("✅ Database initialization completed successfully!")
        logger.info("🚀 System is ready to use!")
        logger.info("📱 Access customer menu at: http://localhost:8000/menu")
        logger.info("🖥️  Access admin panel at: http://localhost:8000/admin")
        logger.info("🍳 Access kitchen panel at: http://localhost:8000/kitchen")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()