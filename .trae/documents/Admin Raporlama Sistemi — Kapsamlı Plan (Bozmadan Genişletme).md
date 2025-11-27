## Hedefler
- Tarih bazlı filtreleme (presetler + özel aralık), detaylı rapor görünümleri.
- Ürün bazlı satış analizi, iptal/iade takibi ve metrikleri.
- Büyük veri için performanslı sorgular ve günlük özet saklama.
- Tablo+grafik görselleştirme; PDF/CSV dışa aktarma; responsive arayüz.
- Mevcut akışı bozmadan modüler ekleme ve Gemini ile akıllı içgörüler.

## Mevcut Kapasite
- API: `GET /api/admin/reports/sales`, `product-matrix`, `closing-report-pdf`, `daily-smart` mevcut ve çalışır.
- AI: `backend/services/ai_service.py` Gemini (`GOOGLE_API_KEY`) ile içgörü üretimini destekliyor.
- UI: Admin → Raporlar sekmesi mevcut; tarih aralığı ve grafik render altyapısı var.

## Veri Modeli (Modüler Özet Tablolar)
- Eklenecek tablolar:
  - `daily_sales_summary(date, total_orders, total_revenue, cancelled_orders, avg_order, created_at)`
  - `daily_product_summary(date, product_id, qty, revenue, created_at)`
- İndeksler: `orders.created_at`, `orders.status`, `order_items.product_id`, `order_items.order_id`.
- Not: Yeni tablolar mevcut şemayı bozmaz; rapor sorgularını hızlandırır.

## Arka Plan Süreçleri
- Snapshot yazıcı endpointleri:
  - `POST /api/admin/reports/snapshot/run?date=YYYY-MM-DD`
  - `POST /api/admin/reports/snapshot/backfill?start_date&end_date`
- Zamanlama: Harici scheduler (cron/Task Scheduler) veya manuel tetikleme.

## API Tasarımı (Yeni Endpoint’ler)
- `GET /api/admin/reports/overview?start_date&end_date`
  - Toplam ciro, sipariş, iptal sayısı; günlük trend; özet tablolara öncelik.
- `GET /api/admin/reports/products?start_date&end_date&limit=10`
  - Ürün bazlı qty/revenue; kategori filtresi opsiyonel.
- `GET /api/admin/reports/cancellations?start_date&end_date`
  - İptal/iade listesi ve toplam tutar etkisi.
- `GET /api/admin/reports/orders?start_date&end_date&status&table&skip&limit`
  - Sipariş detayları; pagination ve sıralama.
- `GET /api/admin/reports/export?format=pdf|csv&start_date&end_date`
  - PDF: mevcut `reportlab` ile; CSV: kütüphanesiz.
- `GET /api/admin/reports/insights?start_date&end_date`
  - Gemini ile akıllı özet/öneriler; mevcut `ai_service` yapılandırmasıyla (`GOOGLE_API_KEY`).

## Frontend (Raporlar Sekmesi Genişletme)
- Filtre modülü: Tarih seçici + preset butonları (“Bugün”, “Dün”, “Son 7 Gün”, “Son 30 Gün”, “Özel”).
- Sekmeler:
  - “Genel Bakış” (KPI kartları + günlük trend chart).
  - “Ürün Analizi” (top ürünler tablo + bar chart).
  - “İptaller” (iptal listesi + toplam iptal tutarı).
  - “Siparişler” (filtrelenebilir & sayfalanabilir tablo).
- Dışa aktarma: PDF (mevcut `closing-report-pdf` ile uyumlu) ve CSV.
- AI içgörü kartı: Gemini’dan gelen öneriler; isteğe bağlı.
- Responsive ve boş durum mesajları; sütun sıralama.

## Sorgu Optimizasyonu
- Tarih aralığı ve durum filtreleriyle yalnız gerekli alanlar.
- Aggregationlarda özet tablolara öncelik; yoksa canlı hesaplama.
- Sipariş listelerinde pagination (`skip/limit`).

## Uyum ve Güvenlik
- Tüm raporlama endpointleri `ADMIN` rolü ile korunur.
- `.env` üzerinden `GOOGLE_API_KEY` (Gemini) kullanımı; key hiçbir yerde loglanmaz.
- Mevcut servislerle geriye uyum; hiçbir mevcut endpoint/akış bozulmaz.

## Uygulama Adımları
1) Özet tablo modellerini ekle ve `create_tables` ile kaydet.
2) Snapshot run/backfill endpointlerini geliştir.
3) Overview/products/cancellations/orders/export/insights API’lerini ekle.
4) Frontend Raporlar sekmesini presetler, sekmeler ve export ile genişlet.
5) Performans testleri (≥10k sipariş) ve indeks doğrulaması.
6) PDF içinde Gemini içgörülerini ek sayfa olarak dahil etme (opsiyonel ayar).

## Teslim Kriterleri
- Filtrelenebilir, presetli, hızlı, detaylı raporlar.
- AI içgörü ve PDF/CSV export çalışır.
- Mevcut akışlar bozulmadan yeni özellikler aktif.

Onayınızla birlikte kod uygulamasına başlayıp, her aşamada doğrulama testlerini yapacağım.