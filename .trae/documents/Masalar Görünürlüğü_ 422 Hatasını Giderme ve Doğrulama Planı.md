## Sorun Analizi
- 422 /api/tables/open: Dinamik rota /{table_id} sabit /open rotasını önden yakalayıp int dönüşümünde başarısız oluyor.
- Dashboard aktif sipariş: Enum değerleri metin karşılaştırmasında yanlış kullanıldığında sayım sıfır kalabiliyor.

## Çözüm Adımları
1) Router Rota Sırası Düzeltmesi
- `backend/routers/tables.py` içinde `@router.get("/open")` rotasını parametreli `@router.get("/{table_id}")` ve diğer dinamik rotalardan önce tanımla.
- Bu rota; aktif siparişleri ve/veya `TableState.is_occupied==True` olan masaları döndürsün.

2) Alias Temizliği (Opsiyonel)
- `backend/main.py` içindeki alias kalabilir; asıl çözüm router içi sabit rota sırasıdır. Çakışma riskini kaldırmak için router rotası öncelikli hale getir.

3) Dashboard Aktif Sipariş Doğrulama
- Enum karşılaştırmasını `o.status.value.lower()` ile yaptığımızı doğrula; aktif statüler: pending/preparing/bekliyor/hazırlanıyor.

4) Frontend Doğrulama
- Admin → Masalar: `loadTables()` çağrısı `GET /api/tables/open`’i kullanıyor; grid dolumunu gözle.
- Dashboard: Açık masalar grid’i ve aktif sipariş kartı değerlerini doğrula.

## Test
- Yeni masa ekle ve siparişle işgal et; `/api/tables/open` 200 ve içerik döner.
- `Hesap Alındı` → `/api/tables/close/{id}` 200, grid ve aktif sayım düşer.
- Mutfak listesi aliası çalıştığı doğrulandı; ek işlem yok.

## Etki
- Mevcut akış bozulmadan stabil görünürlük sağlanır. Rota sırası düzeltmesi geri alınabilir ve minimal değişimdir.

Onay sonrası rota sırasını düzeltecek ve doğrulama testlerini çalıştıracağım.