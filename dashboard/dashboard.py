import os
import json
import requests
from functools import wraps
from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    abort,
    session
)
from dotenv import load_dotenv

load_dotenv(override=True)
    
app = Flask(__name__)
app.secret_key = "rahasia_skripsi_tangguh"

API_BASE = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")
API_URL = f"{API_BASE}/api"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# rute autentikasi
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "username atau password salah!"
            
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


# rute halaman dashboard
@app.route("/")
@login_required
def index():
    try:
        response = requests.get(f"{API_URL}/laporan", timeout=5)
        laporan = [item for item in response.json() if item.get("eskalasi_posko") == True] if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        laporan = []
    
    total = len(laporan)
    menunggu = sum(1 for item in laporan if item["status"] == "Menunggu")
    diproses = sum(1 for item in laporan if item["status"] == "Diproses")
    selesai = sum(1 for item in laporan if item["status"] == "Selesai")

    return render_template(
        "index.html",
        laporan=laporan, total=total, menunggu=menunggu, diproses=diproses, selesai=selesai,
        api_base=API_BASE
    )

@app.route("/daftar-laporan")
@login_required
def daftar_laporan():
    try:
        response = requests.get(f"{API_URL}/laporan", timeout=5)
        if response.status_code == 200:
            laporan = [item for item in response.json() if item.get("eskalasi_posko") == True]
        else:
            laporan = []
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
@login_required
def detail(laporan_id):
    try:
        response = requests.get(
            f"{API_URL}/laporan/{laporan_id}",
            timeout=5
        )
    except requests.exceptions.RequestException:
        abort(404)

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
@login_required
def update_status_laporan(laporan_id):
    status = request.form["status"]

    try:
        requests.put(
            f"{API_URL}/laporan/{laporan_id}/status",
            json={
                "status": status
            },
            timeout=5
        )
    except requests.exceptions.RequestException:
        pass

    return redirect(
        request.referrer or url_for('index')
    )

@app.post("/update-kategori/<int:laporan_id>")
@login_required
def update_kategori_laporan(laporan_id):
    kategori = request.form["kategori"]

    try:
        requests.put(
            f"{API_URL}/laporan/{laporan_id}/kategori",
            json={"kategori": kategori},
            timeout=5
        )
    except requests.exceptions.RequestException:
        pass

    return redirect(request.referrer or url_for('daftar_laporan'))

@app.route("/analysis")
@login_required
def analysis():
    try:
        response = requests.get(f"{API_URL}/laporan", timeout=5)
        if response.status_code == 200:
            laporan = [item for item in response.json() if item.get("eskalasi_posko") == True]
        else:
            laporan = []
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