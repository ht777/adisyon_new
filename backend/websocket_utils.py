"""
WebSocket utilities and broadcast functions
"""
import asyncio
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Global connection manager reference
_connection_manager = None

def set_connection_manager(manager):
    """Set the global connection manager"""
    global _connection_manager
    _connection_manager = manager

def broadcast_order_update(order_data: dict, event_type: str = "order_created"):
    """Sipariş güncellemelerini broadcast et"""
    if not _connection_manager:
        logger.warning("No connection manager available for broadcasting")
        return
        
    message = {
        "type": event_type,
        "data": order_data,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Tüm client'lara gönder
    asyncio.create_task(_connection_manager.broadcast_to_all(message))
    
    # Mutfak ve admin'e özel gönder
    if event_type in ["order_created", "order_updated", "order_status_changed"]:
        asyncio.create_task(_connection_manager.broadcast_to_kitchen(message))
        asyncio.create_task(_connection_manager.broadcast_to_admin(message))

def broadcast_to_all(message: dict):
    """Broadcast message to all connected clients"""
    if _connection_manager:
        asyncio.create_task(_connection_manager.broadcast_to_all(message))

def broadcast_to_kitchen(message: dict):
    """Broadcast message to kitchen clients"""
    if _connection_manager:
        asyncio.create_task(_connection_manager.broadcast_to_kitchen(message))

def broadcast_to_admin(message: dict):
    """Broadcast message to admin clients"""
    if _connection_manager:
        asyncio.create_task(_connection_manager.broadcast_to_admin(message))