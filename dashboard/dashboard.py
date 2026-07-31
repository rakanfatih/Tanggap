import os
import json
import requests
from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    abort
)
from dotenv import load_dotenv, find_dotenv

load_dotenv(override=True)
    
app = Flask(__name__)

API_BASE = os.getenv("FASTAPI_URL", "http://10.103.83.134:8000")
API_URL = f"{API_BASE}/api"
print("DEBUG API_BASE =", API_BASE)

@app.route("/")
def index():
    try:
        response = requests.get(f"{API_URL}/laporan")
        if response.status_code == 200:
            laporan = response.json()
        else:
            laporan = []
    except requests.exceptions.RequestException:
        laporan = []
    
    total = len(laporan)
    
    menunggu = sum(1 for item in laporan if item["status"] == "Menunggu")
    diproses = sum(1 for item in laporan if item["status"] == "Diproses")
    selesai = sum(1 for item in laporan if item["status"] == "Selesai")

    kat_terverifikasi = sum(1 for item in laporan if item["kategori_laporan"] == "insiden terverifikasi")
    kat_tinjauan = sum(1 for item in laporan if item["kategori_laporan"] == "perlu tinjauan")
    kat_bukan = sum(1 for item in laporan if item["kategori_laporan"] == "bukan laporan")

    keparahan_tinggi = 0
    keparahan_sedang = 0
    keparahan_rendah = 0

    for item in laporan:
        if item["intent"] == "lapor_darurat" and item.get("vision_result"):
            try:
                vision_data = json.loads(item["vision_result"])
                sev = vision_data.get("severity", "")
                if sev == "Tinggi":
                    keparahan_tinggi += 1
                elif sev == "Sedang":
                    keparahan_sedang += 1
                elif sev == "Rendah":
                    keparahan_rendah += 1
            except Exception:
                pass

    return render_template(
        "index.html",
        laporan=laporan,
        total=total,
        menunggu=menunggu,
        diproses=diproses,
        selesai=selesai,
        kat_terverifikasi=kat_terverifikasi,
        kat_tinjauan=kat_tinjauan,
        kat_bukan=kat_bukan,
        keparahan_tinggi=keparahan_tinggi,
        keparahan_sedang=keparahan_sedang,
        keparahan_rendah=keparahan_rendah,
        api_base=API_BASE
    )

@app.route("/daftar-laporan")
def daftar_laporan():
    try:
        response = requests.get(f"{API_URL}/laporan")
        laporan = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        laporan = []

    # rekapitulasi
    total = len(laporan)
    menunggu = sum(1 for item in laporan if item["status"] == "Menunggu")
    diproses = sum(1 for item in laporan if item["status"] == "Diproses")
    selesai = sum(1 for item in laporan if item["status"] == "Selesai")
        
    return render_template(
        "laporan.html",
        laporan=laporan,
        api_base=API_BASE
    )

@app.route("/laporan/<int:laporan_id>")
def detail(laporan_id):
    response = requests.get(
        f"{API_URL}/laporan/{laporan_id}"
    )

    if response.status_code != 200:
        abort(404)

    laporan = response.json()

    if laporan.get("vision_result"):
        try:
            laporan["vision_detail"] = json.loads(laporan["vision_result"])
        except Exception:
            laporan["vision_detail"] = {"reason": laporan["vision_result"]}
    else:
        laporan["vision_detail"] = None

    return render_template(
        "detail.html",
        laporan=laporan,
        api_base=API_BASE
    )

@app.post("/update-status/<int:laporan_id>")
def update_status_laporan(laporan_id):
    status = request.form["status"]

    requests.put(
        f"{API_URL}/laporan/{laporan_id}/status",
        json={
            "status": status
        }
    )

    return redirect(
        request.referrer or url_for('index')
    )

@app.route("/analysis")
def analysis():
    try:
        response = requests.get(f"{API_URL}/laporan")
        laporan = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        laporan = []
        
    return render_template(
        "analysis.html",
        laporan=laporan,
        api_base=API_BASE
    )

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )