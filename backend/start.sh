#!/bin/bash

# Restaurant Order System Startup Script

echo "🍽️ Restoran Sipariş Sistemi Başlatılıyor..."

# Backend requirements kontrolü
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt bulunamadı!"
    exit 1
fi

# Python paketlerini yükle
echo "📦 Python paketleri yükleniyor..."
pip install -r requirements.txt

# SQLite veritabanı dosyasını kontrol et
if [ ! -f "restaurant.db" ]; then
    echo "📊 Yeni veritabanı oluşturuluyor..."
fi

# Backend sunucusunu başlat
echo "🚀 Backend sunucusu başlatılıyor..."
echo "🌐 Uygulama http://localhost:8000 adresinde çalışacak"
echo "🔗 Müşteri: http://localhost:8000/static/index.html?table=1"
echo "🔗 Admin: http://localhost:8000/static/admin.html (admin/admin123)"
echo "🔗 Mutfak: http://localhost:8000/static/orders.html"
echo ""
echo "Durdurmak için Ctrl+C'ye basın"
echo ""

# FastAPI sunucusunu başlat
uvicorn main:app --reload --host 0.0.0.0 --port 8000