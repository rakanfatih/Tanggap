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
from dotenv import load_dotenv

load_dotenv()
    
app = Flask(__name__)

API_BASE = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")
API_URL = f"{API_BASE}/api"

@app.route("/")
def index():
    response = requests.get(
        f"{API_URL}/laporan"
    )

    laporan = response.json()
    
    total = len(laporan)
    
    # Disesuaikan dengan mockup Figma
    menunggu = sum(1 for item in laporan if item["status"] == "Menunggu")
    diproses = sum(1 for item in laporan if item["status"] == "Diproses")
    selesai = sum(1 for item in laporan if item["status"] == "Selesai")

    return render_template(
        "index.html",
        laporan=laporan,
        total=total,
        menunggu=menunggu,
        diproses=diproses,
        selesai=selesai,
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
        url_for("index")
    )

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )