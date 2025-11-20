import PyInstaller.__main__
import os
import shutil

print("🚀 PAKETLEME İŞLEMİ BAŞLATILIYOR... (Nihai Çözüm)")

# 1. Temizlik
if os.path.exists("dist"): 
    try: shutil.rmtree("dist")
    except: pass
if os.path.exists("build"): 
    try: shutil.rmtree("build")
    except: pass
if os.path.exists("RestoranAdisyon.spec"): 
    try: os.remove("RestoranAdisyon.spec")
    except: pass

# Frontend klasörünün yolu
current_dir = os.getcwd()
frontend_path = os.path.abspath(os.path.join(current_dir, "..", "frontend"))

# Routers klasörünün yolu (Bunu eklemezsek hata veriyor)
routers_path = os.path.abspath(os.path.join(current_dir, "routers"))

# 2. PyInstaller Komutunu Hazırla
PyInstaller.__main__.run([
    'run.py',                       # Ana dosya
    '--name=RestoranAdisyon',       # Exe adı
    '--onedir',                     # Klasör modu
    '--windowed',                   # Penceresiz
    '--noconfirm',                  # Onay sorma
    '--clean',                      # Önbelleği temizle
    
    # --- KRİTİK: DOSYALARI EKSİKSİZ DAHİL ET ---
    f'--add-data={frontend_path};frontend', # Frontend klasörü
    f'--add-data={routers_path};routers',   # <--- İŞTE BU SATIR EKSİKTİ! (Routers klasörü)
    '--add-data=*.py;.',                    # Ana dizindeki tüm kodlar (main.py, models.py vs.)
    
    # --- KÜTÜPHANELERİ ZORLA AL (Collect All) ---
    '--collect-all=uvicorn',
    '--collect-all=fastapi',
    '--collect-all=sqlalchemy',
    '--collect-all=pydantic',
    '--collect-all=starlette',
    '--collect-all=passlib',        # Şifreleme hatasını çözer
    '--collect-all=bcrypt',
    '--collect-all=email_validator',
    
    # --- GİZLİ IMPORTLAR (Görmezden gelinenleri ekle) ---
    '--hidden-import=engineio.async_drivers.asgi',
    '--hidden-import=passlib.handlers.bcrypt',
    '--hidden-import=routers',              # Router modülünü tanıt
    '--hidden-import=routers.products',     # Alt modülleri tanıt
    '--hidden-import=routers.products_new',
    '--hidden-import=routers.orders',
    '--hidden-import=routers.admin',
    '--hidden-import=routers.auth',
    '--hidden-import=routers.tables',
])

print("\n✅ PAKETLEME TAMAMLANDI!")
print("📂 'dist/RestoranAdisyon' klasörünü masaüstüne alıp test edebilirsiniz.")