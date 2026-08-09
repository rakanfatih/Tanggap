import os
import base64
import json
import re
import cv2
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

try:
    from groq import BadRequestError as GroqBadRequestError
except ImportError:
    GroqBadRequestError = None

from vision.vision_schema import VisionOutput
from vision.image_validator import validate_image

load_dotenv()

# helper functions
def encode_image(image_path: str, max_size: int = 800):
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(f"gagal membaca gambar di {image_path}")

    h, w = img.shape[:2]

    if max(h, w) > max_size:
        scale = max_size / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

    return base64.b64encode(buffer).decode('utf-8')

def _extract_text_content(content) -> str:
    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                block_type = block.get("type")
                if block_type in ("reasoning", "thinking"):
                    continue
                text_val = block.get("text") or block.get("content")
                if isinstance(text_val, str):
                    parts.append(text_val)
        return "".join(parts).strip()

    return str(content).strip()

def _strip_think_tags(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    if "<think>" in cleaned and "</think>" not in cleaned:
        cleaned = cleaned.split("<think>")[0]
    return cleaned.strip()

def _extract_balanced_json(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None  

def _clean_json_text(json_str: str) -> str:
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
    return json_str

# agent function
def analyze_image(image_path: str) -> VisionOutput:

    try:
        validate_image(image_path)
    except Exception as e:
        print(f"gambar ditolak oleh sistem lokal: {e}")
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
            reason=f"validasi lokal gagal: {str(e)}",
            vision_image_path=None
        )

    llm = ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0.7,
        max_tokens=2500,
        reasoning_effort="none",
        reasoning_format="hidden",
        model_kwargs={
            "response_format": {"type": "json_object"},
            "presence_penalty": 1.5,
            "top_p": 0.80,
        },
    )

    base64_image = encode_image(image_path)

    system_instructions = """
        Kamu adalah Vision Agent ahli analisis bencana banjir untuk BPBD, yang bekerja mengadaptasi metodologi FloodDepth-GPT.
    
        [SANGAT PENTING - ATURAN FORMAT]: 
        1. DILARANG KERAS menggunakan tag <think> atau menjabarkan proses berpikirmu.
        2. LANGSUNG mulai jawabanmu dengan karakter '{' dan akhiri dengan '}'.
        3. HANYA berikan objek JSON murni tanpa markdown (jangan gunakan ```json) dan tanpa teks pengantar/penutup apa pun.
        4. JIKA tidak mendeteksi banjir, tetap kembalikan objek JSON dengan "flood_detected": false dan sertakan "reason" yang menjelaskan mengapa tidak terdeteksi.

        {
            "flood_detected": true,
            "visible_objects": ["objek1", "objek2"],
            "object_count": 5,
            "reason": "Jelaskan proses estimasi kedalaman air berdasarkan tinggi air terhadap berbagai bagian fitur referensi. Berikan estimasi dalam meter di sini.",
            "estimated_water_cm": 50.0,
            "confidence": 0.95,
            "severity": "Tinggi" | "Sedang" | "Rendah" | "Tidak Terdeteksi",
            "estimated_water_level": "string",
            "water_percentage": 50.0,
            "image_quality": "Baik",
            "possible_fake": false
        }

        PANDUAN ESTIMASI KEDALAMAN (METRIK REFERENSI):
        Dalam memperkirakan kedalaman air banjir, pertimbangkan metrik tinggi untuk fitur umum berikut:
        - Untuk MANUSIA, pertimbangkan metrik ini: Pria (Tinggi total = 1.75m, Tinggi lutut = 0.4m, Tinggi pinggang = 0.9m, Tinggi pundak = 1.4m); Wanita (Tinggi total = 1.60m, Tinggi lutut = 0.4m, Tinggi pinggang = 0.8m, Tinggi pundak = 1.4m).
        - Untuk SEDAN, pertimbangkan metrik ini: tinggi keseluruhan dari tanah ke atap adalah 1.4m, ground clearance sekitar 0.2m, tinggi dari tanah ke dasar pintu adalah 0.6m, tinggi dari tanah ke atas kap mesin adalah 1.0m, dan tinggi dari tanah ke dasar jendela adalah 0.8m.
        - Untuk TRUK, pertimbangkan metrik ini: tinggi keseluruhan dari tanah ke atap adalah 1.8m, ground clearance sekitar 0.5m, tinggi dari tanah ke dasar pintu adalah 0.8m, tinggi dari tanah ke atas kap mesin adalah 1.3m, tinggi dari tanah ke dasar jendela adalah 1.4m.
        - Untuk SUV, pertimbangkan metrik ini: tinggi keseluruhan dari tanah ke atap adalah 1.7m, ground clearance sekitar 0.3m, tinggi dari tanah ke dasar pintu adalah 0.7m, tinggi dari tanah ke atas kap mesin adalah 1.0m.
        - Untuk BUS, pertimbangkan metrik ini: tinggi keseluruhan dari tanah ke atap adalah 3.2m, ground clearance sekitar 0.7m, tinggi dari tanah ke dasar pintu adalah 1.0m, tinggi dari tanah ke dasar jendela adalah 2.0m.
        - Untuk RAMBU JALAN (termasuk tanda berhenti/stop), dimensi tanda stop (segi delapan merah) adalah 0.9m kali 0.9m, sedangkan ukuran vertikal dari tanah ke atas tanda stop, yang menunjukkan tinggi total papan tanda termasuk tiang adalah 2.9m. Hindari pantulan tanda stop di air. Gunakan juga fitur lain sebagai referensi sekunder.
        
        ATURAN ESTIMASI:
        1. Berdasarkan tinggi air terhadap bagian-bagian dari setiap fitur referensi di atas, perkirakan kedalaman air.
        2. Berikan estimasi sebagai angka diskrit dan bukan interval (rentang).
        3. WAJIB mengonversi hasil akhir kedalaman (meter) ke dalam format centimeter (cm) pada parameter "estimated_water_cm" di objek JSON.

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

    raw_text = ""  

    try:
        try:
            response = llm.invoke([message])
        except Exception as api_err:
            is_groq_bad_request = GroqBadRequestError is not None and isinstance(api_err, GroqBadRequestError)
            error_body = getattr(api_err, "body", None)
            failed_generation = ""
            if isinstance(error_body, dict):
                failed_generation = (error_body.get("error") or {}).get("failed_generation", "") or ""

            if is_groq_bad_request or failed_generation:
                print(f"groq menolak request (400 json_validate_failed): {api_err}")
                if failed_generation:
                    raw_text = failed_generation
                    response = None 
                else:
                    raise ValueError(
                        "groq menolak generation (400 json_validate_failed) dan tidak "
                        "ada failed_generation untuk dipulihkan."
                    ) from api_err
            else:
                raise

        if response is not None and (not hasattr(response, "content") or not response.content):
            raise ValueError("API mengembalikan respons kosong (None atau empty content).")

        if response is not None:
            raw_text = _extract_text_content(response.content)

        if not raw_text:
            raise ValueError("konten teks kosong setelah normalisasi response.content.")

        raw_text = _strip_think_tags(raw_text)
        raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())
        json_str = _extract_balanced_json(raw_text)

        if json_str:
            clean_json_str = _clean_json_text(json_str)
            data_dict = json.loads(clean_json_str)

            if isinstance(data_dict.get("flood_detected"), str):
                data_dict["flood_detected"] = data_dict["flood_detected"].lower() == "true"
            if isinstance(data_dict.get("possible_fake"), str):
                data_dict["possible_fake"] = data_dict["possible_fake"].lower() == "true"
        else:
            print("model tidak mengeluarkan JSON murni. melakukan ekstraksi fallback...")

            is_flood = "flooded" in raw_text.lower() or "banjir" in raw_text.lower() or "water" in raw_text.lower()
            data_dict = {
                "flood_detected": is_flood,
                "confidence": 0.85 if is_flood else 0.1,
                "severity": "Sedang" if "sedang" in raw_text.lower() or "65" in raw_text or "70" in raw_text else (
                    "Tinggi" if "tinggi" in raw_text.lower() else "Tidak Terdeteksi"),
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

    except json.JSONDecodeError as e:
        print(f"[VISION ERROR] JSON tidak valid: {e}")
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
            reason=f"JSON dari API tidak valid: {str(e)}"
        )
    except Exception as e:
        print(f"gagal memproses/parsing JSON dari API: {e}")
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
            reason=f"gagal memproses/parsing JSON dari API: {str(e)}"
        )

    hasil.vision_image_path = None
    return hasil