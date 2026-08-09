import requests
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": "Tanggap-BPBD/1.0 (rakanfatih01@gmail.com)"
}

# helper functions
def cek_cuaca_aktual(lat: float, lon: float):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m"
        "&daily=precipitation_sum"
        "&past_days=1&forecast_days=1"
        "&timezone=auto"
    )

    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return {
                "weather": "tidak diketahui",
                "temperature": None,
                "curah_hujan_mm": 0.0
            }

        data = response.json()
        suhu = data.get("current", {}).get("temperature_2m", None)
        curah_hujan_list = data.get("daily", {}).get("precipitation_sum", [0, 0])
        total_curah_hujan = sum([x for x in curah_hujan_list if x is not None])

        return {
            "weather": "Data Diterima",
            "temperature": suhu,
            "curah_hujan_mm": total_curah_hujan
        }

    except Exception as e:
        print(f"gagal mengambil data cuaca Open-Meteo: {e}")
        return {
            "weather": "Tidak diketahui",
            "temperature": None,
            "curah_hujan_mm": 0.0
        }

def cek_lokasi_aktual(lat: float, lon: float):
    url = (
        "https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}"
        f"&lon={lon}"
        "&format=json"
        "&accept-language=id"
    )

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return {"address": "lokasi tidak ditemukan", "gps_valid": False}

        data = response.json()
        alamat = data.get("display_name", "lokasi tidak ditemukan")
        return {"address": alamat, "gps_valid": True}

    except Exception as e:
        print(f"gagal mengambil data lokasi Nominatim: {e}")
        return {"address": "lokasi tidak diketahui", "gps_valid": False}

def koordinat_valid(lat, lon):
    if lat is None or lon is None: 
        return False

    LAT_MIN, LAT_MAX = -6.380000, -6.080000
    LON_MIN, LON_MAX = 106.680000, 106.980000

    if not (LAT_MIN <= lat <= LAT_MAX) or not (LON_MIN <= lon <= LON_MAX):
        return False

    return True

def klasifikasi_hujan_bmkg(curah_hujan_mm: float):
    if curah_hujan_mm < 0.5:
        return "Tidak Hujan", 0
    elif 0.5 <= curah_hujan_mm < 20:
        return "Hujan Ringan", 10
    elif 20 <= curah_hujan_mm < 50:
        return "Hujan Sedang", 20
    elif 50 <= curah_hujan_mm < 100:
        return "Hujan Lebat", 30
    elif 100 <= curah_hujan_mm <= 150:
        return "Hujan Sangat Lebat", 40
    else:
        return "Hujan Ekstrem", 50

def hitung_validation_score(gps_valid: bool, address: str, skor_hujan: int):
    score = 0

    if gps_valid:
        score += 30 

    if address not in ["lokasi tidak ditemukan", "lokasi tidak diketahui", "koordinat tidak valid"]:
        score += 20  

    score += skor_hujan

    return min(score, 100)

# agent function
def validasi_laporan(user_message: str, lat: float, lon: float):
    gps_valid = koordinat_valid(lat, lon)
    hasil_cuaca = cek_cuaca_aktual(lat, lon)

    if gps_valid:
        hasil_lokasi = cek_lokasi_aktual(lat, lon)
    else:
        hasil_lokasi = {
            "address": "koordinat tidak valid", 
            "gps_valid": False
        }

    kategori_hujan, skor_hujan = klasifikasi_hujan_bmkg(
        hasil_cuaca["curah_hujan_mm"]
    )

    validation_score = hitung_validation_score(
        gps_valid=hasil_lokasi["gps_valid"],
        address=hasil_lokasi["address"],
        skor_hujan=skor_hujan
    )

    hasil = {
        "pesan_asli": user_message,
        "koordinat": {"latitude": lat, "longitude": lon},
        "alamat_lengkap": hasil_lokasi["address"],
        "gps_valid": hasil_lokasi["gps_valid"],
        "suhu": hasil_cuaca["temperature"],
        "curah_hujan_mm": hasil_cuaca["curah_hujan_mm"],
        "kategori_hujan": kategori_hujan,
        "poin_cuaca": skor_hujan,
        "validation_score": validation_score
    }

    return hasil