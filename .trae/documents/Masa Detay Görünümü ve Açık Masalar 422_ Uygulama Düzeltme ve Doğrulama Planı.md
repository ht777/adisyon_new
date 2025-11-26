## Hızlı Kök Neden
- Masa detay penceresinde `${...}` literal görünümü: iç içe template literal + document.write kullanımı kaçış bozukluğu.
- 422 `/api/tables/open`: Router’da `/{table_id}` dinamik rota sabit `/open` rotasını gölgeliyor.

## Yapılacaklar
### 1) Masa Detay Render (Güvenli DOM)
- `openTableDetails(id)` fonksiyonunu DOM API (createElement/append) ile yeniden yaz.
- Şablon string iç içe kullanımını kaldır; tek seviyeli string veya `.textContent` ile veri bağla.
- “Yazdır” butonu: `POST /api/tables/print-bill/{id}` çağırır; müşteri `bill_request` ile geldiğinde de otomatik tetikleme korunsun.

### 2) Açık Masalar 422 Düzeltmesi
- `backend/routers/tables.py` içinde `@router.get("/open")` tanımını dosyanın baş tarafına, tüm dinamik rotalardan önce konumlandır.
- Ana uygulamadaki alias `/api/tables/open` kalır, fakat UI öncelikle router rotasını kullanır.

### 3) Gerçek Zamanlı Senkronizasyon
- WS `table_status` ve `order_*` mesajlarında Dashboard ve Masalar bölümlerini yenile (mevcut toast bildirimi sürdür).
- Sipariş yaratımında `TableState.is_occupied=True`; kapamada `False`.

### 4) Dashboard Aktif Sipariş
- Enum karşılaştırmalarını `status.value.lower()` ile teyit et; aktif: pending/preparing/bekliyor/hazırlanıyor.

### 5) UX ve Responsive
- Detay penceresinde:
  - Üst: masa numarası + geliş zamanı vurgulu
  - Orta: toplam tutar kartı (font-mono)
  - Alt: siparişler tablosu (ürün/adet/fiyat/tutar, notlar)
  - Sağda “Yazdır” butonu
- Grid/tables Tailwind ile responsive düzen (md/lg sütunlar).

### 6) Test/Doğrulama
- Tek/çok siparişli masalar için detay penceresi render ve yazdırma tetiklemesi.
- `/api/tables/open` → 200, grid dolu; sipariş gelince WS ile otomatik görünür.
- “Hesap Alındı” sonrası gridden düşme ve aktif sipariş azalması.
- Ağ kesintisi: WS yeniden bağlanma; manuel “Yenile” ile veri uyumu.

## Etki
- Mevcut akış bozulmadan; geri alınabilir küçük değişikliklerle görünürlük ve render hatası giderilir.

Onay sonrası uygulayıp smoke testlerle doğrulayacağım.