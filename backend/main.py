import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models import create_tables, User, UserRole, RestaurantConfig, get_session
from pathlib import Path
from routers import products_new as products, orders, admin, auth, tables
from sqlalchemy.orm import Session
from models import get_session
from auth import get_password_hash
import json
import asyncio
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager
from websocket_utils import set_connection_manager, broadcast_order_update

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./restaurant.db")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

import sys

# Statik dosyaların yolu (EXE uyumlu)
if getattr(sys, 'frozen', False):
    # Eğer .exe olarak çalışıyorsa
    BASE_DIR = Path(sys.executable).parent
    STATIC_DIR = BASE_DIR / "frontend" / "static"
else:
    # Normal python olarak çalışıyorsa
    BASE_DIR = Path(__file__).resolve().parent
    STATIC_DIR = BASE_DIR.parent / "frontend" / "static"

try:
    from network_utils import set_static_ip
except ImportError:
    def set_static_ip(): return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Restaurant Order System...")
    
    if os.name == 'nt':
        try:
            pass 
        except Exception as e:
            logger.warning(f"IP setup check skipped: {e}")

    # 1. Tabloları Oluştur
    create_tables()
    logger.info("Database tables created/verified")

    # 2. OTOMATİK BAŞLANGIÇ VERİLERİ (Settings dahil)
    db = next(get_session())
    try:
        # A) ADMIN OLUŞTURMA
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.info("⚠️ Admin kullanıcısı bulunamadı. Otomatik oluşturuluyor...")
            new_admin = User(
                username="admin",
                email="admin@restoran.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(new_admin)
            logger.info("✅ Varsayılan admin oluşturuldu: admin / admin123")
        else:
            logger.info("✅ Admin kullanıcısı mevcut.")

        # B) RESTORAN AYARLARINI BAŞLATMA (Ayarların ilk kaydı)
        config = db.query(RestaurantConfig).first()
        if not config:
            logger.info("⚠️ Restoran ayarları bulunamadı. Varsayılan ayarlar oluşturuluyor...")
            default_config = RestaurantConfig()
            db.add(default_config)
            logger.info("✅ Varsayılan restoran ayarları oluşturuldu.")
            
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Başlangıç verisi oluşturma hatası: {e}")
    finally:
        db.close()

    yield
    logger.info("Shutting down Restaurant Order System...")

app = FastAPI(
    title="Restaurant Order System",
    version="1.0.0",
    description="Complete restaurant ordering system",
    debug=DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(tables.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
else:
    logger.warning(f"Static directory not found at: {STATIC_DIR}")

@app.get("/menu")
async def serve_menu():
    return FileResponse(STATIC_DIR / "menu.html")

@app.get("/admin")
async def serve_admin():
    return FileResponse(STATIC_DIR / "admin.html")

@app.get("/kitchen")
async def serve_kitchen():
    return FileResponse(STATIC_DIR / "orders.html")

@app.get("/login")
@app.get("/login.html")
async def serve_login():
    login_path = STATIC_DIR / "login.html"
    if login_path.exists():
         return FileResponse(login_path)
    return FileResponse(STATIC_DIR / "admin.html")

@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "menu.html")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.kitchen_connections: List[WebSocket] = []
        self.admin_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, client_type: str = "customer"):
        self.active_connections.append(websocket)
        if client_type == "kitchen":
            self.kitchen_connections.append(websocket)
        elif client_type == "admin":
            self.admin_connections.append(websocket)
        logger.info(f"WS Connected: {client_type}")

    def disconnect(self, websocket: WebSocket, client_type: str = "customer"):
        if websocket in self.active_connections: self.active_connections.remove(websocket)
        if client_type == "kitchen" and websocket in self.kitchen_connections: self.kitchen_connections.remove(websocket)
        if client_type == "admin" and websocket in self.admin_connections: self.admin_connections.remove(websocket)
        logger.info(f"WS Disconnected: {client_type}")

    async def broadcast_to_all(self, message: dict):
        if self.active_connections:
            await asyncio.gather(*[self.send_message(ws, json.dumps(message)) for ws in self.active_connections], return_exceptions=True)

    async def broadcast_to_kitchen(self, message: dict):
        if self.kitchen_connections:
            await asyncio.gather(*[self.send_message(ws, json.dumps(message)) for ws in self.kitchen_connections], return_exceptions=True)

    async def broadcast_to_admin(self, message: dict):
        if self.admin_connections:
            await asyncio.gather(*[self.send_message(ws, json.dumps(message)) for ws in self.admin_connections], return_exceptions=True)

    async def send_message(self, websocket: WebSocket, message: str):
        try: await websocket.send_text(message)
        except: pass

manager = ConnectionManager()
set_connection_manager(manager)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    client_type = "customer"
    try:
        initial_data = await websocket.receive_text()
        try:
            msg = json.loads(initial_data)
            if msg.get("type") == "register":
                client_type = msg.get("client_type", "customer")
            
            await manager.connect(websocket, client_type)
            
        except json.JSONDecodeError:
            await manager.connect(websocket, client_type)

        while True:
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_type)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_type)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/info")
async def system_info():
    return {"app": "Restaurant System", "status": "running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)