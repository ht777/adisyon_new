#!/bin/bash

# SSL sertifikaları oluşturma scripti
# Bu script geliştirme ortamı için kendinden imzalı sertifikalar oluşturur

SSL_DIR="ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"

# SSL dizinini oluştur
mkdir -p "$SSL_DIR"

# Sertifika ve anahtar oluştur
echo "SSL sertifikaları oluşturuluyor..."

openssl req -x509 -newkey rsa:4096 -keyout "$KEY_FILE" -out "$CERT_FILE" -days 365 -nodes -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Restaurant/CN=localhost"

if [ $? -eq 0 ]; then
    echo "✅ SSL sertifikaları başarıyla oluşturuldu:"
    echo "   - Sertifika: $CERT_FILE"
    echo "   - Anahtar: $KEY_FILE"
    echo ""
    echo "⚠️  UYARI: Bu sertifikalar sadece geliştirme ortamı içindir."
    echo "   Üretim ortamı için güvenilir bir sertifika otoritesinden"
    echo "   sertifika almalısınız."
else
    echo "❌ SSL sertifikaları oluşturulurken hata oluştu."
    exit 1
fi