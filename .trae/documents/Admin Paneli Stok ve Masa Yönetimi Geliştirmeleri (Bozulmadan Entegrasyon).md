## Genel Yaklaşım

* Mevcut FastAPI ve frontend akışı korunur; yeni uçlar alias veya ek uç olarak eklenir.

* Veri alanları eksikse uygulama çökmez: güvenli varsayılan ve türetilmiş değerler kullanılır.

* Backend değişiklikleriyle uyumlu frontend güncellemeleri yapılır (Admin + Mutfak); çalışır bütün halinde teslim edilir.

## Dosya/Dizin Değişiklikleri

* `backend/services/ai_service.py` (yeni): Google Gemini entegrasyonu, `.env` → `GOOGLE_API_KEY` okuma, `generate_analysis_text(matrix_data: list) -> str` (fallback güvenli metin).

* `backend/routers/orders.py`: `GET /api/kitchen-tickets` alias; `POST /api/printer/print-order/{id}` stub; `update_order_status` içine “completed” mantığı (garson ligi puanları).

* `backend/routers/tables.py`: `POST /api/tables/transfer/{source_id}/{target_id}` ve `POST /api/tables/merge/{source_id}/{target_id}` uçları; `is_occupied` ve `merged_with_table_id` mantığı yazılımsal.

* `backend/routers/admin.py`: `GET /api/admin/reports/product-matrix` (Star/Dog matrisi + AI analizi), `GET /api/admin/reports/closing-report-pdf` (ReportLab PDF, FileResponse).

* `backend/routers/auth.py`: `POST /api/auth/pin-login` (4 haneli `quick_password` doğrulama → JWT).

* Bağımlılıklar: `google-generativeai` ve `reportlab` eklenir; `.env`’e `GOOGLE_API_KEY`.

## Backend Uygulama Adımları

### AI Servisi

1. `ai_service.py` içinde Gemini istemcisi; `.env`’den anahtar okuma.
2. `generate_analysis_text(matrix_data)` Türkçe 3 eyleme dönük öneri üretir; hata/key yoksa statik öneri döner.

### Mutfak & Yazıcı

1. `GET /api/kitchen-tickets`: `GET /api/orders/kitchen/pending` çıktısını döner; her öğe için `created_at` kesin mevcut.
2. `POST /api/printer/print-order/{id}`: Şimdilik stub; log kaydı ve 200 yanıt.

### Masa Transfer & Birleştirme

1. `POST /api/tables/transfer/{source_id}/{target_id}`: Tamamlanmamış siparişleri taşır; `is_occupied` bayraklarını günceller.
2. `POST /api/tables/merge/{source_id}/{target_id}`: Kaynağı hedefe birleşmiş olarak işaretler; alan yoksa yazılımsal state ile çalışır.

### Garson Ligi

1. `update_order_status`: Durum `COMPLETED`/`TESLIM_EDILDI` olduğunda sipariş `total_amount` ve `tip_amount` (yoksa 0) alınır.
2. `waiter_id` kullanıcı puanlarına eklenir: `total_sales_score` ve `total_tips_collected` artar (alanlar yoksa null-safe hesap ve ileride migrasyon planı).

### Raporlama & PDF

1. `GET /api/admin/reports/product-matrix`: Kâr (`price - cost`) ve hacme (satış adet) göre Star/Dog sınıflaması; AI analizi eklenir.
2. `GET /api/admin/reports/closing-report-pdf`: ReportLab ile PDF (Toplam Ciro, Toplam Bahşiş, En Çok Satanlar, AI metni); `FileResponse`.

### PIN Girişi

1. `POST /api/auth/pin-login`: 4 haneli `quick_password` doğrulama ve JWT üretimi; alan yoksa güvenli alternatif doğrulama.

## Frontend Güncellemeleri

* Admin Panel:

  * Dashboard veya ayrı “Garson Ligi” bölümü: en çok satış/tip toplayanlar listesi (yeni uçlarla beslenen).

  * Raporlar: “Ürün Matrisi” çağrısı ve AI metninin gösterimi; “Kapanış PDF” indirme butonu.

* Mutfak Ekranı:

  * Gerekirse `kitchen-tickets` uç kullanımına uyum; mevcut görünüm ve timer hesapları korunur.

* Menü:

  * Sipariş akışı korunur; ek değişiklik yok.

## Doğrulama

* Smoke test: sipariş → kitchen tickets → printer stub → transfer/merge → completed sonrası puan artışı → product-matrix JSON + PDF → pin-login.

* WebSocket bildirimleri ve mevcut akışlar bozulmadan çalışır.

## Dağıtım & Konfig

* Yeni bağımlılıkların yüklenmesi; `.env`’de `GOOGLE_API_KEY`.

* Üretim ortamında CORS ve `SECRET_KEY` mevcut ayarlara dokunmadan sürdürülür.

