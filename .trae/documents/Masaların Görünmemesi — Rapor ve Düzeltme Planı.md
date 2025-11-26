## Rapor
- Beklenen: Dashboard ve Admin → Masalar sekmesindeki “Açık Masalar” alanları yalnızca aktif ve açık (sipariş veya dolu) masaları göstermeli.
- Mevcut Davranış: Açık masalar görünmüyor.
- İlgili mantık:
  - Model: `is_active` alanı görünürlüğü belirler (backend/models.py:105).
  - Dashboard/Masalar grid: `GET /api/tables/open-list` yalnızca (a) aktif (`is_active==True`) ve (b) aktif siparişi olan veya `TableState.is_occupied==True` masaları listeler (backend/main.py:187–214).
  - Soft delete: `DELETE /api/tables/{id}` masayı pasife çeker (`is_active=False`), bu yüzden açık listede görünmez (backend/routers/tables.py:154–163).
  - Sipariş oluşturma, masayı dolu (occupied) işaretler: (backend/routers/orders.py:155–161).
- Olası kök nedenler:
  - Masalar pasife çekilmiş (`is_active=False`) olduğu için açık-list filtrelerine takılıyor.
  - Masalarda aktif sipariş yok ya da siparişler “delivered/cancelled” durumunda; `open-list` bu durumda listemez.
  - `TableState.is_occupied` hiç set edilmemiş (siparişler başka yoldan oluşturulduysa), doluluk bilinmiyor.

## Çözüm Planı (Sadece aktif ve açık masaları gösterecek şekilde)
### Kontrol ve Diagnostik
- Admin’de hızlı diagnostik: `GET /api/tables/stats/summary` çağrısını kullanarak toplam aktif masa, aktif (son 2 saatte siparişli) masa ve müsait masa sayısını göster.
- Gözlem: Eğer aktif masa sayısı 0 ise, masalar pasif olabilir; eğer aktif masa >0 ama açık masa 0 ise sipariş/doluluk kriterlerini karşılayan yoktur.

### Frontend İyileştirmeleri
- Dashboard ve Masalar’daki “Açık Masalar” gridlerine boş durum (empty-state) mesajı ekle: “Hiç açık masa yok”. Bu, UI’nin sessiz boş kalmasını engeller.
- Masalar sekmesinde küçük bir “Aktifleştir” yardımcı alanı ekle: Masa numarasını girip ilgili masayı yeniden aktif et (arkada `GET /api/tables?active_only=false` ile id eşleştir, ardından `PUT /api/tables/{id}` body `{is_active:true}` gönder). Liste yine aktifleri gösterecek.

### Doğrulama
- En az bir aktif masa için bir sipariş oluştur (orders API mevcut) ve `TableState.is_occupied=True` set edildiğini doğrula; açık masalar gridinde görünmelidir.
- Bir masayı `DELETE` ile pasife çek, açık gridten kaybolduğunu doğrula; “Aktifleştir” ile geri getir ve tekrar göründüğünü kontrol et.

### Beklenen Sonuç
- Dashboard ve Masalar sekmesindeki açık masalar listesi yalnızca aktif ve açık masaları güvenilir biçimde gösterir.
- Pasif hale gelen masalar kolayca tekrar aktifleştirilebilir; boş durumda kullanıcı bilgilendirilir.

Onaylarsanız, sadece frontend tarafında (`frontend/static/admin.html`) boş durum mesajını ve “Aktifleştir” yardımcı alanını ekleyerek ilerleyeceğim; backend varsayılan filtreleri korunacak, açık masa gösterimi mevcut iş kurallarına (aktif + sipariş/doluluk) bağlı kalacaktır.