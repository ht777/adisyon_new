import os
import importlib
from typing import List

def generate_analysis_text(matrix_data: List[dict]) -> str:
    key = os.getenv("GOOGLE_API_KEY", "")
    try:
        if not key:
            raise RuntimeError("missing key")
        genai = importlib.import_module("google.generativeai")
        genai.configure(api_key=key)
        prompt = (
            "Bu restoran menü performans verisini analiz et ve işletme sahibine "
            "Türkçe, kısa ve uygulanabilir 3 öneri ver. Veri: " + str(matrix_data)
        )
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        text = getattr(resp, "text", None)
        if not text:
            try:
                text = "".join([p.text for p in resp.candidates[0].content.parts])
            except Exception:
                text = None
        if not text:
            raise RuntimeError("empty")
        return text.strip()
    except Exception:
        return (
            "1) En çok satan ürünlerin porsiyon ve sunum hızını artırın.\n"
            "2) Düşük hacimli ürünlerde kampanya veya çapraz satış deneyin.\n"
            "3) Kârlı ürünleri menüde öne çıkarıp stok takibini sıklaştırın."
        )
def generate_ai_answer(prompt: str, context: dict) -> str:
    key = os.getenv("GOOGLE_API_KEY", "")
    try:
        if not key:
            raise RuntimeError("missing key")
        genai = importlib.import_module("google.generativeai")
        genai.configure(api_key=key)
        txt = (
            "Aşağıdaki restoran verilerine göre yönetici sorusunu yanıtla. "
            "Türkçe ve kısa, uygulanabilir cevap ver.\n\n" +
            "Veri: " + str(context) + "\n\nSoru: " + prompt
        )
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(txt)
        text = getattr(resp, "text", None)
        if not text:
            try:
                text = "".join([p.text for p in resp.candidates[0].content.parts])
            except Exception:
                text = None
        if not text:
            raise RuntimeError("empty")
        return text.strip()
    except Exception:
        return "Veriler temelinde: Ciroyu artırmak için kampanya, stok optimizasyonu ve menüde kârlı ürün odak önerilir."
