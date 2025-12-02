import os
import importlib
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Logger ayarla
logger = logging.getLogger("ai_service")

def _get_gemini_response(prompt: str) -> str:
    """Gemini API'den yanıt al"""
    # Her çağrıda .env'den tekrar oku (güvenlik için)
    load_dotenv(override=True)
    key = os.getenv("GOOGLE_API_KEY", "")
    
    logger.info(f"GOOGLE_API_KEY durumu: {'Tanımlı' if key else 'Tanımlı değil'}")
    
    if not key:
        logger.warning("GOOGLE_API_KEY bulunamadı - varsayılan analiz kullanılacak")
        raise RuntimeError("GOOGLE_API_KEY bulunamadı")
    
    try:
        genai = importlib.import_module("google.generativeai")
        genai.configure(api_key=key)
        
        # Farklı model isimlerini dene (güncel modeller)
        model_names = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-pro-latest"]
        resp = None
        last_error = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                logger.info(f"Model {model_name} başarılı")
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model_name} başarısız: {str(e)[:100]}")
                continue
        
        if resp is None:
            raise last_error or RuntimeError("Hiçbir model çalışmadı")
        
        text = getattr(resp, "text", None)
        if not text:
            try:
                text = "".join([p.text for p in resp.candidates[0].content.parts])
            except Exception:
                text = None
        if not text:
            raise RuntimeError("Boş yanıt")
        return text.strip()
    except ImportError:
        logger.error("google-generativeai modülü yüklü değil")
        raise RuntimeError("AI modülü yüklü değil")
    except Exception as e:
        logger.error(f"Gemini API hatası: {str(e)}")
        raise

def generate_analysis_text(matrix_data: List[dict]) -> str:
    try:
        prompt = (
            "Bu restoran menü performans verisini analiz et ve işletme sahibine "
            "Türkçe, kısa ve uygulanabilir 3 öneri ver. Veri: " + str(matrix_data)
        )
        return _get_gemini_response(prompt)
    except Exception:
        return (
            "1) En çok satan ürünlerin porsiyon ve sunum hızını artırın.\n"
            "2) Düşük hacimli ürünlerde kampanya veya çapraz satış deneyin.\n"
            "3) Kârlı ürünleri menüde öne çıkarıp stok takibini sıklaştırın."
        )

def generate_ai_answer(prompt: str, context: dict) -> str:
    try:
        txt = (
            "Aşağıdaki restoran verilerine göre yönetici sorusunu yanıtla. "
            "Türkçe ve kısa, uygulanabilir cevap ver.\n\n" +
            "Veri: " + str(context) + "\n\nSoru: " + prompt
        )
        return _get_gemini_response(txt)
    except Exception:
        return "Veriler temelinde: Ciroyu artırmak için kampanya, stok optimizasyonu ve menüde kârlı ürün odak önerilir."

def generate_daily_report_analysis(data: Dict[str, Any]) -> str:
    """Günlük kapanış raporu için AI analizi"""
    try:
        prompt = f"""Sen profesyonel bir restoran danışmanısın. Bugünkü işletme verilerini analiz et.

📅 TARİH: {data.get('date', 'Bugün')}

💰 FİNANSAL ÖZET:
- Toplam Ciro: {data.get('total_revenue', 0):.2f} ₺
- Nakit: {data.get('cash_total', 0):.2f} ₺
- Kredi Kartı: {data.get('card_total', 0):.2f} ₺
- Toplam Sipariş: {data.get('total_orders', 0)}
- İptal Edilen: {data.get('cancelled_orders', 0)}
- Ortalama Sepet: {data.get('avg_order', 0):.2f} ₺

🏆 EN ÇOK SATANLAR:
{data.get('top_products_text', 'Veri yok')}

📉 EN AZ SATANLAR:
{data.get('low_products_text', 'Veri yok')}

👨‍🍳 GARSON PERFORMANSI:
{data.get('waiter_stats_text', 'Veri yok')}

📦 STOK DURUMU:
{data.get('stock_status_text', 'Veri yok')}

🪑 MASA BİLGİSİ:
- Aktif Masa Sayısı: {data.get('total_tables', 0)}

Lütfen Türkçe olarak:
1. Günün genel değerlendirmesini yap (2-3 cümle)
2. Öne çıkan olumlu noktaları belirt
3. Dikkat edilmesi gereken konuları belirt
4. Yarın için 2-3 uygulanabilir öneri ver
"""
        return _get_gemini_response(prompt)
    except Exception as e:
        logger.warning(f"Günlük AI analizi başarısız: {str(e)}")
        # Fallback: Basit analiz oluştur
        revenue = data.get('total_revenue', 0)
        orders = data.get('total_orders', 0)
        avg = data.get('avg_order', 0)
        cancelled = data.get('cancelled_orders', 0)
        
        analysis = f"""📊 GÜNLÜK ÖZET ANALİZİ

💰 Bugünkü Performans:
• Toplam ciro: {revenue:.2f} ₺
• Sipariş sayısı: {orders}
• Ortalama sepet: {avg:.2f} ₺
• İptal oranı: {(cancelled/max(1,orders)*100):.1f}%

📈 Değerlendirme:
"""
        if revenue > 0:
            if avg > 100:
                analysis += "• Ortalama sepet tutarı iyi seviyede.\n"
            else:
                analysis += "• Ortalama sepet tutarını artırmak için çapraz satış önerilir.\n"
            
            if cancelled > orders * 0.1:
                analysis += "• İptal oranı yüksek, sebepleri araştırılmalı.\n"
            else:
                analysis += "• İptal oranı kabul edilebilir seviyede.\n"
        else:
            analysis += "• Bugün için yeterli veri bulunmuyor.\n"
        
        analysis += "\n💡 AI analizi için GOOGLE_API_KEY tanımlanmalıdır."
        return analysis

def generate_weekly_report_analysis(data: Dict[str, Any]) -> str:
    """Haftalık rapor için AI analizi"""
    try:
        prompt = f"""Sen profesyonel bir restoran danışmanısın. Bu haftanın işletme verilerini analiz et.

📅 DÖNEM: {data.get('start_date', '')} - {data.get('end_date', '')}

💰 HAFTALIK FİNANSAL ÖZET:
- Toplam Ciro: {data.get('total_revenue', 0):.2f} ₺
- Toplam Sipariş: {data.get('total_orders', 0)}
- İptal Sayısı: {data.get('cancelled_orders', 0)}
- Ortalama Günlük Ciro: {data.get('avg_daily_revenue', 0):.2f} ₺
- Ortalama Sepet: {data.get('avg_order', 0):.2f} ₺

📊 GÜNLÜK DAĞILIM:
{data.get('daily_breakdown_text', 'Veri yok')}

🏆 HAFTANIN EN ÇOK SATANLARI:
{data.get('top_products_text', 'Veri yok')}

📉 HAFTANIN EN AZ SATANLARI:
{data.get('low_products_text', 'Veri yok')}

👨‍🍳 GARSON PERFORMANSI:
{data.get('waiter_stats_text', 'Veri yok')}

📈 ÖNCEKI HAFTAYA GÖRE:
- Ciro Değişimi: {data.get('revenue_change', 0):.1f}%
- Sipariş Değişimi: {data.get('order_change', 0):.1f}%

Lütfen Türkçe olarak:
1. Haftanın genel performans değerlendirmesi (3-4 cümle)
2. En iyi ve en kötü günleri belirle, nedenlerini tahmin et
3. Ürün performans analizi yap
4. Garson performansını değerlendir
5. Gelecek hafta için 3-5 stratejik öneri ver
"""
        return _get_gemini_response(prompt)
    except Exception as e:
        logger.warning(f"Haftalık AI analizi başarısız: {str(e)}")
        revenue = data.get('total_revenue', 0)
        orders = data.get('total_orders', 0)
        avg_daily = data.get('avg_daily_revenue', 0)
        change = data.get('revenue_change', 0)
        
        analysis = f"""📊 HAFTALIK ÖZET ANALİZİ

💰 Bu Haftanın Performansı:
• Toplam ciro: {revenue:.2f} ₺
• Toplam sipariş: {orders}
• Günlük ortalama: {avg_daily:.2f} ₺
• Önceki haftaya göre: {"↑" if change >= 0 else "↓"} {abs(change):.1f}%

📈 Değerlendirme:
"""
        if change >= 10:
            analysis += "• Ciro önceki haftaya göre önemli ölçüde arttı. Başarılı bir hafta!\n"
        elif change >= 0:
            analysis += "• Ciro stabil seyrediyor.\n"
        else:
            analysis += "• Ciro düşüşü var, kampanya veya promosyon düşünülebilir.\n"
        
        analysis += "\n💡 Detaylı AI analizi için GOOGLE_API_KEY tanımlanmalıdır."
        return analysis

def generate_monthly_report_analysis(data: Dict[str, Any]) -> str:
    """Aylık rapor için AI analizi"""
    try:
        prompt = f"""Sen profesyonel bir restoran danışmanısın. Bu ayın işletme verilerini kapsamlı analiz et.

📅 DÖNEM: {data.get('start_date', '')} - {data.get('end_date', '')}

💰 AYLIK FİNANSAL ÖZET:
- Toplam Ciro: {data.get('total_revenue', 0):.2f} ₺
- Toplam Sipariş: {data.get('total_orders', 0)}
- İptal Sayısı: {data.get('cancelled_orders', 0)}
- Ortalama Günlük Ciro: {data.get('avg_daily_revenue', 0):.2f} ₺
- Ortalama Sepet: {data.get('avg_order', 0):.2f} ₺

📊 HAFTALIK DAĞILIM:
{data.get('weekly_breakdown_text', 'Veri yok')}

🏆 AYIN EN ÇOK SATANLARI:
{data.get('top_products_text', 'Veri yok')}

📉 AYIN EN AZ SATANLARI:
{data.get('low_products_text', 'Veri yok')}

👨‍🍳 GARSON PERFORMANSI:
{data.get('waiter_stats_text', 'Veri yok')}

📈 ÖNCEKI AYA GÖRE:
- Ciro Değişimi: {data.get('revenue_change', 0):.1f}%
- Sipariş Değişimi: {data.get('order_change', 0):.1f}%

📦 STOK ANALİZİ:
{data.get('stock_analysis_text', 'Veri yok')}

Lütfen Türkçe olarak:
1. Ayın genel performans değerlendirmesi (4-5 cümle)
2. Trend analizi: Yükselen ve düşen trendler
3. En başarılı ve en sorunlu alanları belirle
4. Ürün portföyü önerileri (menüden çıkarılacak/eklenmesi gereken)
5. Personel ve operasyon önerileri
6. Gelecek ay için 5 stratejik hedef ve aksiyon planı
"""
        return _get_gemini_response(prompt)
    except Exception as e:
        logger.warning(f"Aylık AI analizi başarısız: {str(e)}")
        revenue = data.get('total_revenue', 0)
        orders = data.get('total_orders', 0)
        avg_daily = data.get('avg_daily_revenue', 0)
        change = data.get('revenue_change', 0)
        
        analysis = f"""📊 AYLIK ÖZET ANALİZİ

💰 Bu Ayın Performansı:
• Toplam ciro: {revenue:.2f} ₺
• Toplam sipariş: {orders}
• Günlük ortalama: {avg_daily:.2f} ₺
• Önceki aya göre: {"↑" if change >= 0 else "↓"} {abs(change):.1f}%

📈 Değerlendirme:
"""
        if change >= 15:
            analysis += "• Ciro önceki aya göre önemli ölçüde arttı. Harika bir ay!\n"
        elif change >= 0:
            analysis += "• Ciro stabil seyrediyor, büyüme fırsatları değerlendirilebilir.\n"
        elif change >= -10:
            analysis += "• Hafif ciro düşüşü var, kampanya stratejileri gözden geçirilmeli.\n"
        else:
            analysis += "• Önemli ciro düşüşü var, acil aksiyon planı gerekli.\n"
        
        analysis += """
💡 Öneriler:
• En çok satan ürünleri öne çıkarın
• Düşük performanslı ürünleri değerlendirin
• Personel motivasyonunu artırın
• Müşteri geri bildirimlerini toplayın

⚠️ Detaylı AI analizi için GOOGLE_API_KEY tanımlanmalıdır."""
        return analysis
