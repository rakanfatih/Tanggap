import os
import requests
from dotenv import load_dotenv

load_dotenv()

# VALIDASI CUACA  
def cek_cuaca_aktual(lat: float, lon: float) -> str:
    #ambil data cuaca dari openweathermap
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key or api_key == "masukkan api key weather di sini":
        return "simulasi cuaca: hujan lebat"
    
    #endpoint api openweathermap
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=id"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code == 200:
            cuaca = data['weather'][0]['description']
            suhu = data['main']['temp']
            return f"{cuaca.capitalize()}, Suhu: {suhu}°C"
        else:
            return f"gagal mengambil cuaca: {data.get('message', 'error tidak diketahui')}"
    except Exception as e:
        return f"terjadi kesalahan koneksi: {e}"

#VALIDASI LOKASI
def cek_lokasi_aktual(lat: float, lon: float) -> str:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    # fallback  
    if not api_key or api_key == "masukkan api key google maps di sini":
        return "Simulasi Lokasi: Jl. Margonda Raya, Kota Depok, Jawa Barat"
    
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if data['status'] == 'OK':
            alamat_lengkap = data['results'][0]['formatted_address']
            return alamat_lengkap
        elif data['status'] == 'ZERO_RESULTS':
            return "gagal dilacak: Lokasi fiktif atau tidak terdaftar di peta (kemungkinan koordinat palsu)."
        else:
            return f"gagal melacak lokasi: Status {data['status']}"
    except Exception as e:
        return f"terjadi kesalahan koneksi peta: {e}"
    
def validasi_laporan(user_message: str, lat: float, lon: float):
    #verifikasi laporan berdasarkan lokasi dan cuaca
    print(f"agen validator sedang mengecek titik koordinat [{lat}, {lon}]...")

    #panggil function cek cuaca
    status_cuaca = cek_cuaca_aktual(lat, lon)
    alamat_lokasi = cek_lokasi_aktual(lat, lon)

    print(f"[VALIDATOR] Hasil dari satelit OpenWeather: {status_cuaca}")
    print(f"[VALIDATOR] Hasil Pelacakan Peta : {alamat_lokasi}")

    is_hujan = any(kata in status_cuaca.lower() for kata in ["hujan", "gerimis", "lebat", "badai"])
    is_lokasi_nyata = "gagal" not in alamat_lokasi.lower()

    if is_hujan and is_lokasi_nyata:
        tingkat_validitas = "tinggi"
        print("[VALIDATOR] Kesimpulan: Valid (Cuaca Mendukung & Lokasi Nyata)")
    else:
        tingkat_validitas = "rendah (terindikasi hoax)"
        print("[VALIDATOR] Kesimpulan: INDIKASI HOAX (Cuaca Cerah / Lokasi Fiktif)")

    hasil_validasi = {
        "pesan_asli": user_message,
        "koordinat_gps": f"[{lat}, {lon}]",
        "alamat_lengkap": alamat_lokasi,      
        "kondisi_cuaca_aktual": status_cuaca,
        "status_validasi": tingkat_validitas
    }

    return hasil_validasi