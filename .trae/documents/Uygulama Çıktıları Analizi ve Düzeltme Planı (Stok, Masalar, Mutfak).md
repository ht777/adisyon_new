## Sorun Özeti (Log Analizi)
- 422 /api/tables/open: Parametreli rota ile çakışma
  - Nedeni: `tables` router’da önce tanımlanan `GET /{table_id}` rotası `open` sözcüğünü `int`’e parse edemediği için 422 dönüyor.
  - Kanıt: Loglarda tüm `/api/tables/open` çağrıları 422.
- 404 /api/kitchen-tickets: Endpoint yolu yanlış
  - Nedeni: Backend’te rota `GET /api/orders/kitchen-tickets`. Frontend `/api/kitchen-tickets` çağırıyor.
  - Kanıt: Loglarda tekrar tekrar 404.
- 422 PUT /api/products/{id}: Kısmi update desteklenmiyor
  - Nedeni: `update_product` `ProductCreate` şemasını bekliyor; frontend yalnızca `stock` veya `track_stock` gönderiyor. Eksik zorunlu alanlar yüzünden 422.
  - Kanıt: Loglarda `PUT /api/products/{id}` için 422.
- 404 statik logo: Dosya yok
  - Nedeni: `restaurant_logo.png`/`logo.png` bulunmuyor. UI fallback var; kritik değil.

## Düzeltme Planı
### 1) Masalar: `/open` rotayı çakışmadan kurtarma
- `backend/routers/tables.py` içinde sabit rotaları parametreli rotalardan önce tanımla.
- Alternatif: Üstte `@router.get("/open")` ve altta `@router.get("/{table_id}")` kalsın. Gerekirse ayırıcı path: `/stats/open`.
- Etki: `Masalar` sekmesi ve `Dashboard` üst panel artık 200 döner.

### 2) Mutfak Biletleri: Alias ekleme
- `backend/routers/orders.py` içine prefix olmadan veya ana `main.py` içinde `GET /api/kitchen-tickets` alias ekle; `GET /api/orders/kitchen-tickets` ile aynı veriyi döndür.
- Etki: Mutfak ve Admin UI’daki mevcut çağrılar 404 yerine 200 döner.

### 3) Ürün Update: Kısmi güncellemeyi destekle
- `ProductUpdate` şeması ekle: tüm alanlar Opsiyonel.
- `update_product` imzasında `ProductUpdate` kullan ve `exclude_unset=True` ile yalnızca gönderilen alanları set et.
- `StockMovement` ek mantığı korunur; yalnızca `stock` ve/veya `track_stock` değişiminde kayıt atılır.
- Etki: Stok yönetim ekranındaki `PUT /api/products/{id}` çağrıları 200.

### 4) Statik Logo
- Opsiyonel: UI logo yükleme akışında fallback’i koru. İleride `/static/uploads/restaurant_logo.png` oluşturulduğunda 404 kalkar.

### 5) Test ve Doğrulama
- Masalar: `/api/tables/open` 200, grid doluyor; “Hesap Alındı” butonu → `/api/tables/close/{id}` 200.
- Mutfak: `/api/kitchen-tickets` 200, mutfak ekranı listeliyor.
- Stok: `PUT /api/products/{id}` yalnızca `stock`/`track_stock` ile 200; kritik stokta WS toast.
- Dashboard: düşük stok paneli ve açık masalar grid’i düzgün render.

## Dosya Bazlı İşler
- `backend/routers/tables.py`:
  - `GET /open` tanımı `GET /{table_id}`’den önce gelecek şekilde taşınır.
- `backend/main.py` veya `backend/routers/orders.py`:
  - `GET /api/kitchen-tickets` alias eklenir; mevcut veri üretim fonksiyonuna delege edilir.
- `backend/routers/products_new.py`:
  - `ProductUpdate` şeması eklenir ve `update_product` kısmi update mantığına alınır.

## Risiko ve Geri-Alınabilirlik
- Rota sırası değişikliği yalnızca 422’leri kaldırır; mevcut davranış değişmez.
- Alias eklemek backward-compatible.
- Kısmi update, mevcut tam update akışını bozmaz; yalnızca esneklik ekler.

## Son
Onaydan sonra bu üç düzeltmeyi uygulayıp smoke testleri çalıştıracağım; ardından üretim senaryosunda da doğrulama önerilerini ekleyeceğim.