import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api"

# Admin credentials
ADMIN_AUTH = ("admin", "admin123")

def create_sample_products():
    """Create sample products for testing"""
    
    sample_products = [
        {
            "name": "Margherita Pizza",
            "description": "Klasik İtalyan pizzası, domates sos, mozzarella peyniri, taze fesleğen",
            "price": 89.90,
            "discounted_price": 79.90,
            "category": "Pizza",
            "features": {"vegan": False, "popular": True, "spicy": False},
            "stock": 20
        },
        {
            "name": "Vegan Sebze Dürüm",
            "description": "Taze sebzeler, humus ve tahin soslu sağlıklı dürüm",
            "price": 65.00,
            "category": "Dürüm",
            "features": {"vegan": True, "popular": False, "spicy": False},
            "stock": 15
        },
        {
            "name": "Acılı Tavuk Burger",
            "description": "Baharatlı tavuk göğsü, özel sos, marul, domates",
            "price": 75.50,
            "category": "Burger",
            "features": {"vegan": False, "popular": True, "spicy": True},
            "stock": 25
        },
        {
            "name": "Çikolatalı Brownie",
            "description": "Sıcak servis edilen yoğun çikolatalı brownie, vanilya dondurma",
            "price": 45.00,
            "category": "Tatlı",
            "features": {"vegan": False, "popular": True, "spicy": False},
            "stock": 30
        },
        {
            "name": "Köri Soslu Sebze Kızartması",
            "description": "Hint baharatlarıyla marine edilmiş sebzeler, köri sos",
            "price": 55.00,
            "category": "Aperitif",
            "features": {"vegan": True, "popular": False, "spicy": True},
            "stock": 18
        },
        {
            "name": "Limonata",
            "description": "Taze sıkılmış limon, buz, nane yaprakları",
            "price": 25.00,
            "category": "İçecek",
            "features": {"vegan": True, "popular": True, "spicy": False},
            "stock": 50
        }
    ]
    
    print("🍽️ Örnek ürünler oluşturuluyor...")
    
    for i, product in enumerate(sample_products):
        try:
            response = requests.post(f"{BASE_URL}/products", json=product)
            if response.status_code == 200:
                print(f"✅ {product['name']} oluşturuldu")
            else:
                print(f"❌ {product['name']} oluşturulamadı: {response.status_code}")
        except Exception as e:
            print(f"❌ {product['name']} hatası: {e}")
    
    print("\n📊 Ürün listesi:")
    try:
        response = requests.get(f"{BASE_URL}/products")
        if response.status_code == 200:
            products = response.json()['products']
            for product in products:
                print(f"- {product['name']} (₺{product['price']}) - Stok: {product['stock']}")
    except Exception as e:
        print(f"Ürün listesi alınamadı: {e}")

def create_qr_codes():
    """Create QR codes for sample tables"""
    print("\n📱 Örnek QR kodlar oluşturuluyor...")
    
    for table_number in range(1, 6):
        try:
            response = requests.get(f"{BASE_URL}/qr?table={table_number}", auth=ADMIN_AUTH)
            if response.status_code == 200:
                print(f"✅ Masa {table_number} QR kodu oluşturuldu")
            else:
                print(f"❌ Masa {table_number} QR kodu oluşturulamadı: {response.status_code}")
        except Exception as e:
            print(f"❌ Masa {table_number} QR kodu hatası: {e}")

if __name__ == "__main__":
    print("🚀 Restoran Sipariş Sistemi - Test Verileri Oluşturma")
    print("=" * 60)
    
    create_sample_products()
    create_qr_codes()
    
    print("\n🎉 Test verileri oluşturma tamamlandı!")
    print("\nŞimdi şu adresleri test edebilirsiniz:")
    print("- Müşteri: http://localhost:8000/static/index.html?table=1")
    print("- Admin: http://localhost:8000/static/admin.html")
    print("- Mutfak: http://localhost:8000/static/orders.html")