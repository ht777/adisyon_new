@echo off
REM Restaurant Ordering System Deployment Script (Windows)
REM Bu script sistemi Docker ile başlatır

setlocal enabledelayedexpansion

echo 🚀 Restaurant Ordering System Deployment Script
echo ==============================================

REM Renkli çıktı için (Windows 10+)
set RED=[31m
set GREEN=[32m
set YELLOW=[33m
set NC=[0m

REM Docker kontrolü
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker bulunamadı. Lütfen Docker'ı yükleyin.
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker Compose bulunamadı. Lütfen Docker Compose'u yükleyin.
    exit /b 1
)

echo ✅ Docker ve Docker Compose bulundu.

REM Port kontrolü
set ports=80 443 8000 5432 6379
for %%p in (%ports%) do (
    netstat -an | findstr ":%%p " | findstr "LISTEN" >nul
    if !errorlevel! equ 0 (
        echo ⚠️  Port %%p zaten kullanımda.
        set /p continue=Devam etmek istiyor musunuz? (y/N): 
        if /i "!continue!" neq "y" exit /b 1
    )
)

REM SSL sertifikaları kontrolü
if not exist "ssl\cert.pem" or not exist "ssl\key.pem" (
    echo 🔐 SSL sertifikaları oluşturuluyor...
    call generate-ssl.bat
) else (
    echo ✅ SSL sertifikaları zaten mevcut.
)

REM .env dosyası kontrolü
if not exist ".env" (
    echo 📄 .env dosyası oluşturuluyor...
    copy .env.example .env
    echo ⚠️  Lütfen .env dosyasını düzenleyin ve SECRET_KEY değerini değiştirin.
    set /p edit_now=.env dosyasını şimdi düzenlemek istiyor musunuz? (y/N): 
    if /i "!edit_now!"=="y" (
        notepad .env
    )
) else (
    echo ✅ .env dosyası zaten mevcut.
)

REM Docker container'ları başlat
echo 🏗️  Docker container'ları başlatılıyor...

docker-compose down
docker-compose up -d --build

echo ⏳ Servislerin hazır olması bekleniyor...
timeout /t 30 /nobreak >nul

REM Servislerin durumunu kontrol et
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ Sistem başarıyla başlatıldı!
    echo 📱 Müşteri Menüsü: https://localhost/menu
    echo 🖥️  Admin Paneli: https://localhost/admin
    echo 🍳 Mutfak Paneli: https://localhost/kitchen
    echo 📊 API Dokümantasyonu: https://localhost/docs
) else (
    echo ❌ Container'lar başlatılamadı. Logları kontrol edin:
    docker-compose logs
    exit /b 1
)

echo.
echo Deployment tamamlandı!
pause