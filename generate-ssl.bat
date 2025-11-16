@echo off
REM SSL sertifikaları oluşturma scripti (Windows)
REM Bu script geliştirme ortamı için kendinden imzalı sertifikalar oluşturur

set SSL_DIR=ssl
set CERT_FILE=%SSL_DIR%\cert.pem
set KEY_FILE=%SSL_DIR%\key.pem

REM SSL dizinini oluştur
if not exist "%SSL_DIR%" mkdir "%SSL_DIR%"

REM Sertifika ve anahtar oluştur
echo SSL sertifikaları oluşturuluyor...

REM OpenSSL Windows'ta yüklü mü kontrol et
where openssl >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ OpenSSL bulunamadı. Lütfen OpenSSL'i yükleyin.
    echo    https://slproweb.com/products/Win32OpenSSL.html adresinden indirebilirsiniz.
    exit /b 1
)

openssl req -x509 -newkey rsa:4096 -keyout "%KEY_FILE%" -out "%CERT_FILE%" -days 365 -nodes -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Restaurant/CN=localhost"

if %errorlevel% equ 0 (
    echo ✅ SSL sertifikaları başarıyla oluşturuldu:
    echo    - Sertifika: %CERT_FILE%
    echo    - Anahtar: %KEY_FILE%
    echo.
    echo ⚠️  UYARI: Bu sertifikalar sadece geliştirme ortamı içindir.
    echo    Üretim ortamı için güvenilir bir sertifika otoritesinden
    echo    sertifika almalısınız.
) else (
    echo ❌ SSL sertifikaları oluşturulurken hata oluştu.
    exit /b 1
)

pause