import os
import requests
from dotenv import load_dotenv

load_dotenv()

def cek_cuaca_aktual(lat: float, lon: float) -> str:
    """mengambil data cuaca realtime dari openweathermap"""
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key or api_key == "masukkan api key weather di sini":
        return "simulasi cuaca: hujan lebat"
    
    #endpoint api openweathermap
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=id"

    try:
        response = request.get(url)
        data = response.json()

        if response.status_code == 200:
            cuaca = data['weather'][0]['description']
            suhu = data['main']['temp']
            return f"{cuaca.capitalize()}, Suhu: {suhu}°C"
        else:
            return f"gagal mengambil cuaca: {data.get('message', 'error tidak diketahui')}"
    except Exception as e:
        return f"terjadi kesalahan konksi: {e}"
    
def validasi_laporan(pesan: str, lat: float, lon: float):
    """agen validator memverifikasi laporan berdasarkan lokasi dan cuaca"""
    print(f"agen validator sedang mengecek titik koordinat [{lat}, {lon}]...")

    #panggil function cek cuaca
    status_cuaca = cek_cuaca_aktual(lat, lon)

    #logika validasi
    #kalau cuaca hujan/gerimis = valid:tinggi
    #kalau cerah = mungkin banjir kiriman = valid:sedang
    if "hujan" in status_cuaca.lower() or "gerimis" in status_cuaca.lower():
        tingkat_validitas = "tinggi"
    else:
        tingkat_validitas = "sedang"

    #kembalikan enrched data
    hasil_validasi ={
        "pesan_asli": pesan,
        "koordinat_gps": f"[{lat}, {lon}]",
        "kondisi_cuaca_aktual": status_cuaca,
        "status_validasi": tingkat_validitas
    }

    return hasil_validasi

#uji lokal
if __name__ == "__main__":
    #skenario: warga menekan tombol 'lapor bencana'
    #aplikasi mengirimkan pesan dan koordinat ke sistem

    pesan_masuk = "Tolong, air sudah masuk rumah saya, saya terjebak di lantai 2, butuh bantuan evakuasi!"

    #contoh koordinat gps
    lat_warga = -6.1601
    lon_warga = 106.7416

    print("-" * 40)
    data_tervalidasi = validasi_laporan(pesan_masuk, lat_warga, lon_warga)

    print("\n--- HASIL VALIDASI LAPORAN ---")
    for kunci, nilai in data_tervalidasi.items():
        print(f"{kunci.replace('_', ' ').title()}: {nilai}")