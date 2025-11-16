@echo off
echo 🍽️ Restoran Sipariş Sistemi Baslatiliyor...

echo 📦 Python paketleri yükleniyor...
pip install -r requirements.txt

echo 📊 Veritabani kontrol ediliyor...

echo 🚀 Backend sunucusu başlatiliyor...
echo 🌐 Uygulama http://localhost:8000 adresinde çalişacak
echo 🔗 Müşteri: http://localhost:8000/static/index.html?table=1
echo 🔗 Admin: http://localhost:8000/static/admin.html (admin/admin123)
echo 🔗 Mutfak: http://localhost:8000/static/orders.html
echo.
echo Durdurmak için Ctrl+C'ye basin
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause