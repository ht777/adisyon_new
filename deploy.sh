#!/bin/bash

# Restaurant Ordering System Deployment Script
# Bu script sistemi Docker ile başlatır

set -e

echo "🚀 Restaurant Ordering System Deployment Script"
echo "=============================================="

# Renkli çıktı için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonksiyonlar
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker bulunamadı. Lütfen Docker'ı yükleyin.${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose bulunamadı. Lütfen Docker Compose'u yükleyin.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker ve Docker Compose bulundu.${NC}"
}

check_ports() {
    local ports=(80 443 8000 5432 6379)
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Port $port zaten kullanımda.${NC}"
            read -p "Devam etmek istiyor musunuz? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    done
}

generate_ssl() {
    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
        echo -e "${YELLOW}🔐 SSL sertifikaları oluşturuluyor...${NC}"
        chmod +x generate-ssl.sh
        ./generate-ssl.sh
    else
        echo -e "${GREEN}✅ SSL sertifikaları zaten mevcut.${NC}"
    fi
}

create_env_file() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}📄 .env dosyası oluşturuluyor...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Lütfen .env dosyasını düzenleyin ve SECRET_KEY değerini değiştirin.${NC}"
        read -p ".env dosyasını şimdi düzenlemek istiyor musunuz? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        fi
    else
        echo -e "${GREEN}✅ .env dosyası zaten mevcut.${NC}"
    fi
}

deploy() {
    echo -e "${YELLOW}🏗️  Docker container'ları başlatılıyor...${NC}"
    
    # Stop existing containers
    docker-compose down
    
    # Build and start services
    docker-compose up -d --build
    
    # Wait for services to be ready
    echo -e "${YELLOW}⏳ Servislerin hazır olması bekleniyor...${NC}"
    sleep 30
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✅ Sistem başarıyla başlatıldı!${NC}"
        echo -e "${GREEN}📱 Müşteri Menüsü: https://localhost/menu${NC}"
        echo -e "${GREEN}🖥️  Admin Paneli: https://localhost/admin${NC}"
        echo -e "${GREEN}🍳 Mutfak Paneli: https://localhost/kitchen${NC}"
        echo -e "${GREEN}📊 API Dokümantasyonu: https://localhost/docs${NC}"
    else
        echo -e "${RED}❌ Container'lar başlatılamadı. Logları kontrol edin:${NC}"
        docker-compose logs
        exit 1
    fi
}

show_logs() {
    echo -e "${YELLOW}📋 Container logları:${NC}"
    docker-compose logs -f
}

stop_services() {
    echo -e "${YELLOW}🛑 Servisler durduruluyor...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Servisler durduruldu.${NC}"
}

show_status() {
    echo -e "${YELLOW}📊 Container durumu:${NC}"
    docker-compose ps
}

# Ana menü
show_menu() {
    echo ""
    echo "Restaurant Ordering System - Deployment Menu"
    echo "============================================="
    echo "1) 🚀 Sistemi başlat"
    echo "2) 🛑 Sistemi durdur"
    echo "3) 📊 Durumu görüntüle"
    echo "4) 📋 Logları görüntüle"
    echo "5) 🔧 SSL sertifikalarını yeniden oluştur"
    echo "6) 🗑️  Tüm verileri temizle (dikkatli olun!)"
    echo "7) ❌ Çıkış"
    echo ""
}

cleanup() {
    echo -e "${RED}⚠️  Tüm veriler silinecek! Bu işlem geri alınamaz.${NC}"
    read -p "Devam etmek istiyor musunuz? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker system prune -f
        echo -e "${GREEN}✅ Tüm veriler temizlendi.${NC}"
    fi
}

# Ana program
main() {
    check_docker
    
    if [ "$1" == "--quick" ]; then
        echo -e "${YELLOW}⚡ Hızlı başlatma modu...${NC}"
        check_ports
        generate_ssl
        create_env_file
        deploy
        exit 0
    fi
    
    while true; do
        show_menu
        read -p "Seçiminiz: " choice
        
        case $choice in
            1)
                check_ports
                generate_ssl
                create_env_file
                deploy
                ;;
            2)
                stop_services
                ;;
            3)
                show_status
                ;;
            4)
                show_logs
                ;;
            5)
                generate_ssl
                echo -e "${YELLOW}🔄 Container'lar yeniden başlatılıyor...${NC}"
                docker-compose restart nginx
                ;;
            6)
                cleanup
                ;;
            7)
                echo -e "${GREEN}👋 Güle güle!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Geçersiz seçim. Lütfen tekrar deneyin.${NC}"
                ;;
        esac
        
        echo ""
        read -p "Devam etmek için Enter tuşuna basın..."
        clear
    done
}

# Scripti başlat
main "$@"