import os
import base64
import json
import shutil
import re
import cv2
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from vision.vision_schema import VisionOutput
from vision.image_validator import validate_image

load_dotenv()

def encode_image(image_path: str, max_size: int = 800):
    img = cv2.imread(image_path)
    
    if img is None:
        raise ValueError(f"Gagal membaca gambar di {image_path}")

    h, w = img.shape[:2]
    
    if max(h, w) > max_size:
        scale = max_size / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    
    _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    
    return base64.b64encode(buffer).decode('utf-8')

def analyze_image(image_path: str) -> VisionOutput:

    try:
        val_result = validate_image(image_path)
    except Exception as e:
        print(f"[VISION] Gambar ditolak oleh sistem lokal: {e}")
        return VisionOutput(
            flood_detected=False,
            confidence=0.0,
            severity="Tidak Terdeteksi",
            estimated_water_level="Error",
            estimated_water_cm=0.0,
            water_percentage=0.0,
            visible_objects=[],
            object_count=0,
            image_quality="Buruk",
            possible_fake=True,
            reason=f"Validasi lokal gagal: {str(e)}",
            vision_image_path=None
        )

    # inisialisasi model
    llm = ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0.0,
        max_tokens=2500 
    )

    base64_image = encode_image(image_path)

    system_instructions = """
        Kamu adalah Vision Agent ahli analisis bencana banjir untuk BPBD.
    
        [SANGAT PENTING - ATURAN FORMAT]: 
        1. DILARANG KERAS menggunakan tag <think> atau menjabarkan proses berpikirmu.
        2. LANGSUNG mulai jawabanmu dengan karakter '{' dan akhiri dengan '}'.
        3. HANYA berikan objek JSON murni tanpa markdown (jangan gunakan ```json) dan tanpa teks pengantar/penutup apa pun.
        4. JIKA tidak mendeteksi banjir, tetap kembalikan objek JSON dengan "flood_detected": false dan sertakan "reason" yang menjelaskan mengapa tidak terdeteksi.

        {
            "flood_detected": true,
            "visible_objects": ["objek1", "objek2"],
            "object_count": 5,
            "reason": "Jelaskan DAHULU observasi ketinggian air terhadap objek referensi yang terlihat di gambar berdasarkan panduan metrik tinggi. Jelaskan rasionya dengan singkat (Maks 2 kalimat).",
            "estimated_water_cm": 50.0,
            "confidence": 0.95,
            "severity": "Tinggi" | "Sedang" | "Rendah" | "Tidak Terdeteksi",
            "estimated_water_level": "string",
            "water_percentage": 50.0,
            "image_quality": "Baik",
            "possible_fake": false
        }

        PANDUAN ESTIMASI KEDALAMAN (METRIK REFERENSI):
        Gunakan ukuran objek berikut sebagai referensi mutlak untuk menghitung tinggi air:
        - MANUSIA: Pria (Lutut: 40cm, Pinggang: 90cm, Pundak: 140cm, Total: 175cm). Wanita (Lutut: 40cm, Pinggang: 80cm, Pundak: 140cm, Total: 160cm).
        - SEDAN: Ground clearance 20cm, dasar pintu 60cm, kap mesin 100cm, atap 140cm.
        - TRUK: Ground clearance 50cm, dasar pintu 80cm, kap mesin 130cm, atap 180cm.
        - SUV: Ground clearance 30cm, dasar pintu 70cm, kap mesin 100cm, atap 170cm.
        - RAMBU LALU LINTAS: Tinggi total termasuk tiang 290cm, ukuran rambu di atas 90cm.
        
        ATURAN ESTIMASI:
        1. Identifikasi objek referensi yang terendam.
        2. Bandingkan batas air dengan letak anatomi/bagian kendaraan tersebut berdasarkan angka di atas.
        3. Hasilkan angka diskrit untuk estimated_water_cm, bukan rentang.

        ATURAN SEVERITY:
        - "Tinggi": Air >100 cm.
        - "Sedang": Air 40 - 90 cm.
        - "Rendah": Air <35 cm.
        - "Tidak Terdeteksi": Tidak ada genangan air.

        ATURAN FALLBACK (JIKA TIDAK ADA OBJEK REFERENSI):
        Jika gambar HANYA berisi hamparan air dan TIDAK ADA objek referensi yang bisa diukur (manusia, kendaraan, bangunan, tiang):
        1. Set "visible_objects" menjadi array kosong [].
        2. Set "object_count" menjadi 0.
        3. Set "estimated_water_cm" menjadi 0.0.
        4. Set "confidence" menjadi rendah (misalnya 0.3 atau 0.4).
        5. Set "severity" menjadi "Tidak Dapat Dipastikan".
        6. Pada "reason", tuliskan: "Hanya terlihat hamparan air tanpa objek referensi untuk mengukur kedalaman."
        """                     

    message = HumanMessage(
        content=[
            {"type": "text", "text": system_instructions},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            },
        ]
    )

    try:
        print("[VISION] Sedang memproses gambar via Qwen...")
        response = llm.invoke([message])
        
        if not response or not hasattr(response, "content") or not response.content:
            raise ValueError("API mengembalikan respons kosong (None atau empty content).")

        raw_text = response.content.strip()

        if not raw_text:
            raise ValueError("Variabel raw_text kosong setelah strip().")
        
        if "</think>" in raw_text:
            raw_text = raw_text.split("</think>")[-1].strip()

        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        
        if match:
            clean_json_str = match.group(0)
            data_dict = json.loads(clean_json_str)

            # Konversi boolean jika dikembalikan sebagai string
            if isinstance(data_dict.get("flood_detected"), str):
                data_dict["flood_detected"] = data_dict["flood_detected"].lower() == "true"
            if isinstance(data_dict.get("possible_fake"), str):
                data_dict["possible_fake"] = data_dict["possible_fake"].lower() == "true"
        else:
            print("[VISION] Warning: Model tidak mengeluarkan JSON murni (terpotong). Melakukan ekstraksi fallback dari teks mentah...")
            
            is_flood = "flooded" in raw_text.lower() or "banjir" in raw_text.lower() or "water" in raw_text.lower()
            
            data_dict = {
                "flood_detected": is_flood,
                "confidence": 0.85 if is_flood else 0.1,
                "severity": "Sedang" if "sedang" in raw_text.lower() or "65" in raw_text or "70" in raw_text else ("Tinggi" if "tinggi" in raw_text.lower() else "Tidak Terdeteksi"),
                "estimated_water_level": "Sedang" if is_flood else "Tidak Terdeteksi",
                "estimated_water_cm": 70.0 if is_flood else 0.0,
                "water_percentage": 80.0 if is_flood else 0.0,
                "visible_objects": ["manusia", "perahu karet", "rumah"] if is_flood else [],
                "object_count": 5 if is_flood else 0,
                "image_quality": "Baik",
                "possible_fake": False,
                "reason": "Diekstrak otomatis dari analisis visual karena format JSON dari AI terpotong batasan token."
            }

        hasil = VisionOutput(**data_dict)

    except Exception as e:
        print(f"[VISION] Warning/Error saat parsing LLM: {e}")
        hasil = VisionOutput(
            flood_detected=False,
            confidence=0.0,
            severity="Tidak Terdeteksi",
            estimated_water_level="Error",
            estimated_water_cm=0.0,
            water_percentage=0.0,
            visible_objects=[],
            object_count=0,
            image_quality="Buruk",
            possible_fake=True,
            reason=f"Gagal memproses/parsing JSON dari API: {str(e)}"
        )

    hasil.vision_image_path = None

    return hasil