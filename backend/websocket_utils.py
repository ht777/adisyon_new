import json
import asyncio

# Global connection manager reference
# main.py içindeki manager nesnesine buradan erişeceğiz
manager = None

def set_connection_manager(connection_manager):
    """Main.py tarafından çağrılır ve manager'ı set eder"""
    global manager
    manager = connection_manager

async def broadcast_order_update(message: dict, update_type: str = "order_updated"):
    """
    Sipariş güncellemelerini (yeni sipariş, durum değişimi) ilgili herkese duyurur.
    """
    if manager:
        full_message = {
            "type": update_type,
            "data": message
        }
        # 1. Mutfağa gönder (Sipariş düştü sesi için)
        await manager.broadcast_to_kitchen(full_message)
        
        # 2. Admine gönder (Takip için)
        await manager.broadcast_to_admin(full_message)
        
        # 3. Müşterilere gönder (Sipariş durumu değişti bildirimi için)
        # Not: İdeal dünyada sadece o masaya gönderilmeli ama şimdilik broadcast OK.
        await manager.broadcast_to_all(full_message)

async def broadcast_to_admin(message: dict):
    """
    SADECE Admin paneline mesaj gönderir.
    Örn: Garson Çağrısı, Acil Durum, Sistem Hatası
    """
    if manager:
        # message objesi { "type": "waiter_call", "table_name": "...", "message": "..." } formatında olmalı
        await manager.broadcast_to_admin(message)