import os
import requests
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": "Tanggap-BPBD/1.0 (rakanfatih01@gmail.com)"
}

# cek cuaca
def cek_cuaca_aktual(lat: float, lon: float):

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key or api_key == "masukkan api key weather di sini":
        return {
            "weather": "simulasi hujan lebat",
            "temperature": 28,
            "is_raining": True
        }

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}"
        f"&appid={api_key}"
        "&units=metric"
        "&lang=id"
    )

    try:

        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code != 200:

            return {
                "weather": "tidak diketahui",
                "temperature": None,
                "is_raining": False
            }

        cuaca = data["weather"][0]["description"]
        suhu = data["main"]["temp"]

        kata_hujan = [
            "hujan",
            "gerimis",
            "lebat",
            "badai",
            "rain",
            "drizzle",
            "storm",
            "thunderstorm"
        ]

        is_raining = any(
            kata in cuaca.lower()
            for kata in kata_hujan
        )

        return {
            "weather": cuaca.capitalize(),
            "temperature": suhu,
            "is_raining": is_raining
        }

    except Exception as e:

        print(f"[VALIDATOR] Error cuaca: {e}")

        return {
            "weather": "Tidak diketahui",
            "temperature": None,
            "is_raining": False
        }

# cek lokasi
def cek_lokasi_aktual(lat: float, lon: float):

    url = (
        "https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}"
        f"&lon={lon}"
        "&format=json"
        "&accept-language=id"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:

            return {
                "address": "lokasi tidak ditemukan",
                "gps_valid": False
            }

        data = response.json()

        alamat = data.get(
            "display_name",
            "lokasi tidak ditemukan"
        )

        return {
            "address": alamat,
            "gps_valid": True
        }

    except Exception as e:

        print(e)

        return {
            "address": "lokasi tidak diketahui",
            "gps_valid": False
        }

def koordinat_valid(lat, lon):

    if lat is None or lon is None:
        return False

    if lat < -90 or lat > 90:
        return False

    if lon < -180 or lon > 180:
        return False

    return True


# hitung skor
def hitung_validation_score(
    gps_valid: bool,
    is_raining: bool,
    address: str
):

    score = 0

    if gps_valid:
        score += 40

    if is_raining:
        score += 30

    if address not in [
        "lokasi tidak ditemukan",
        "lokasi tidak diketahui",
        "koordinat tidak valid"
    ]:
        score += 30

    return score

# validator agen
def validasi_laporan(
    user_message: str,
    lat: float,
    lon: float
):
    
    gps_valid = koordinat_valid(lat, lon)
    hasil_cuaca = cek_cuaca_aktual(lat, lon)

    if gps_valid:
        hasil_lokasi = cek_lokasi_aktual(lat, lon)
    else:
        hasil_lokasi = {
            "address": "koordinat tidak valid",
            "gps_valid": False
        }

    validation_score = hitung_validation_score(
        gps_valid=hasil_lokasi["gps_valid"],
        is_raining=hasil_cuaca["is_raining"],
        address=hasil_lokasi["address"]
    )

    hasil = {
        "pesan_asli": user_message,
        "koordinat": {"latitude": lat,"longitude": lon},
        "alamat_lengkap": hasil_lokasi["address"],
        "gps_valid": hasil_lokasi["gps_valid"],
        "kondisi_cuaca": hasil_cuaca["weather"],
        "suhu": hasil_cuaca["temperature"],
        "is_hujan": hasil_cuaca["is_raining"],
        "validation_score": validation_score
    }

    return hasil

# test
if __name__ == "__main__":

    hasil = validasi_laporan(
        user_message="Rumah saya kebanjiran.",
        lat=-6.200000,
        lon=106.816666
    )

    print("\n===== OUTPUT =====")

    print(hasil)