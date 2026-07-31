import os
import base64
import json
import shutil
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from vision.vision_schema import VisionOutput
from vision.image_validator import validate_image

load_dotenv()

def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path: str) -> VisionOutput:
    print("\n==============================")
    print("[VISION AGENT - QWEN V2]")
    print("==============================")

    try:
        val_result = validate_image(image_path)
        print(f"[VISION] Gambar valid. Resolusi: {val_result['width']}x{val_result['height']}")
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
        max_tokens=2048 
    )

    base64_image = encode_image(image_path)

    system_instructions = """
    Kamu adalah Vision Agent ahli analisis bencana banjir untuk BPBD.
    Analisis foto secara ringkas, langsung berikan respons HANYA DALAM FORMAT JSON murni tanpa penjelasan panjang di luar JSON, sesuai dengan skema berikut:
    {
      "flood_detected": true,
      "confidence": 0.95,
      "severity": "Tinggi" | "Sedang" | "Rendah" | "Tidak Terdeteksi",
      "estimated_water_level": "string",
      "estimated_water_cm": 50.0,
      "water_percentage": 50.0,
      "visible_objects": ["objek1", "objek2"],
      "object_count": 5,
      "image_quality": "Baik",
      "possible_fake": false,
      "reason": "penjelasan singkat"
    }

    PANDUAN ESTIMASI KEDALAMAN:
    - Amati proporsi air pada objek referensi terdekat secara objektif.
    - Hasilkan angka diskrit untuk estimated_water_cm (contoh: 30.0, 50.0), bukan rentang.

    ATURAN SEVERITY:
    - "Tinggi": Air merendam lebih dari setengah tinggi manusia (>100 cm).
    - "Sedang": Air merendam sebatas lutut hingga pinggang (40 - 90 cm).
    - "Rendah": Air merendam area bawah seperti mata kaki atau betis (<35 cm).
    - "Tidak Terdeteksi": Tidak ada genangan air.
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
        print(f"[DEBUG] Raw text mentah: {repr(raw_text)}")

        if not raw_text:
            raise ValueError("Variabel raw_text kosong setelah strip().")
        
        if "</think>" in raw_text:
            raw_text = raw_text.split("</think>")[-1].strip()

        if "```json" in raw_text:
            parts = raw_text.split("```json")
            if len(parts) > 1:
                raw_text = parts[1].split("```")[0].strip()
        elif "```" in raw_text:
            parts = raw_text.split("```")
            if len(parts) > 1:
                raw_text = parts[1].strip()

        raw_text = raw_text.strip()
        
        if not raw_text:
            raise ValueError("Teks JSON habis setelah dibersihkan dari markdown/tag.")

        data_dict = json.loads(raw_text)

        if isinstance(data_dict.get("flood_detected"), str):
            data_dict["flood_detected"] = data_dict["flood_detected"].lower() == "true"
        if isinstance(data_dict.get("possible_fake"), str):
            data_dict["possible_fake"] = data_dict["possible_fake"].lower() == "true"

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

    base_name = os.path.basename(image_path)
    name, ext = os.path.splitext(base_name)
    vision_filename = f"{name}_vision{ext}" 
    vision_image_path = os.path.join(os.path.dirname(image_path), vision_filename)
    
    if not os.path.exists(vision_image_path):
        shutil.copy(image_path, vision_image_path)

    hasil.vision_image_path = vision_image_path

    print("\n===== HASIL VISION (QWEN) =====")
    print(f"Flood Detected   : {hasil.flood_detected}")
    print(f"Confidence       : {hasil.confidence}")
    print(f"Severity         : {hasil.severity}")
    print(f"Estimated Water  : {hasil.estimated_water_cm} cm")
    print(f"Water Area       : {hasil.water_percentage} %")
    print(f"Objects Found    : {hasil.object_count} {hasil.visible_objects}")
    print(f"Possible Fake    : {hasil.possible_fake}")
    print(f"Reason           : {hasil.reason}")
    print("=========================")

    return hasil