## Kök Neden Analizi
- Masa Detay Penceresi: Yeni açılan pencerede HTML, iç içe şablon stringler (template literals) kullanılarak `document.write` ile yazıldı. İç içe backtick kullanımı ve `map(...).join('')` yerleştirmelerinde kaçış hataları nedeniyle `${...}` yer tutucular literal metin olarak render edildi; bu yüzden tablo içinde `${d.table_number}` vb. ifadeler görünür hale geldi.
- Açık Masalar 422: `GET /api/tables/open` sabit rotası, router içindeki dinamik `/{table_id}` ile aynı segment altında tanımlandığında yönlendirme sırasında önce dinamik rota yakalanıp int parse edilmek istendi; “open” parse edilemeyince 422 döndü. Ana uygulamadaki alias bu sorunu her zaman maskelemedi; router sırası kritik.

## Düzeltme Stratejisi (Mevcut Akışı Bozmadan)
1) Masa Detay HTML Render
- `openTableDetails` fonksiyonunda DOM tabanlı oluşturma kullan (createElement/append), iç içe template literal’lerden kaçın.
- Alternatif: Tek katmanlı template literal kullan, iç içe backtick yerine dize birleştirme (`+`) ile `map(...).join('')` çıktısını ekle.
- “Yazdır” butonu, admin tarafı `POST /api/tables/print-bill/{id}` uçunu çağırır; müşteri tarafından `bill_request` geldiğinde de tetikleme korunur.

2) `/api/tables/open` Kararlılık
- Router’da sabit rota `@router.get("/open")` tanımını dosyanın üst bölümünde, tüm dinamik rotalardan önce konumlandır.
- Ana uygulamadaki alias kalabilir; ancak UI yalnız router rotasına çağrı yapsın.

3) Dashboard Aktif Sipariş
- Enum karşılaştırmaları `o.status.value.lower()` olarak teyit edilir; aktif durumlar pending/preparing/bekliyor/hazırlanıyor.

4) Gerçek Zamanlı Senkronizasyon
- WS `table_status` mesajı alındığında Dashboard ve Masalar sekmelerini yenilemeye devam et; küçük toast bildirimi göster.

5) Test Planı
- Tek masa: sipariş oluştur → masa otomatik aktif, Dashboard/Masalar grid dolu, detay penceresi tüm kalemleri ve toplamı gösterir.
- Çok siparişli masa: performans ve render doğrulaması, scroll ve gruplama görünür.
- Müşteri “Hesap İste” → `bill_request` ile yazdırma tetiklenir; admin “Yazdır” da manuel tetikler.
- Ağ kesintisi: WS yeniden bağlanır; manuel “Yenile” ile veri tutarlılığı korunur.

## Etki ve Geri-Alınabilirlik
- DOM tabanlı detay render mevcut akışı bozmaz; `document.write` bağımlılığı kalkar ve güvenli hale gelir.
- Rota sırası değişikliği backward-compatible’dir. Gerektiğinde hızlı geri alınabilir.

Onaydan sonra bu düzeltmeleri uygulayıp birlikte görüntü ve 422 hatasını tamamen ortadan kaldıracak smoke testleri çalıştıracağım.