import sys
import os
import time
import webbrowser
import multiprocessing
from threading import Timer

# --- KRİTİK: ÇALIŞMA DİZİNİNİ DÜZELT ---
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
    os.chdir(base_path)
    sys.path.insert(0, base_path)

    sys.stderr = open(os.path.join(base_path, "hata_kaydi.txt"), "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_path)

# --- İMPORTLAR ---
import uvicorn

try:
    from main import app
except ImportError as e:
    print(f"IMPORT HATASI: {e}", file=sys.stderr)
    print(f"Mevcut Dizin: {os.getcwd()}", file=sys.stderr)
    print(f"Dosyalar: {os.listdir(os.getcwd())}", file=sys.stderr)
    raise e

try:
    from network_utils import set_static_ip
except:
    pass

# ---------------------------
#   OTOMATİK 2 SAYFA AÇICI
# ---------------------------
def open_browser():
    time.sleep(3)
    try:
        # Admin sayfası
        webbrowser.open("http://localhost:8000/admin")
        time.sleep(1)
        # Mutfak sayfası
        webbrowser.open("http://localhost:8000/kitchen")  # ← kendi mutfak endpoint’ini yaz
    except:
        pass

# ---------------------------
#         MAIN
# ---------------------------
if __name__ == "__main__":
    multiprocessing.freeze_support()

    try:
        if os.name == 'nt':
            pass
    except:
        pass

    t = Timer(2.0, open_browser)
    t.daemon = True
    t.start()

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, use_colors=False, log_config=None)
    except Exception as e:
        print(f"SUNUCU HATASI: {e}", file=sys.stderr)
