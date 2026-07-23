import requests
from flask import(
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    abort
)
    
app = Flask(__name__)

API_URL = "http://127.0.0.1:8000/api"

@app.route("/")
def index():

    response = requests.get(
        f"{API_URL}/laporan"
    )

    laporan = response.json()
    total = len(laporan)
    terverifikasi = sum(
        1
        for item in laporan
        if item["kategori_laporan"] == "insiden terverifikasi"
    )

    review = sum(
        1
        for item in laporan
        if item["kategori_laporan"] == "perlu tinjauan"
    )

    bukan = sum(
        1
        for item in laporan
        if item["kategori_laporan"] == "bukan laporan"
    )

    return render_template(
        "index.html",
        laporan=laporan,
        total=total,
        terverifikasi=terverifikasi,
        review=review,
        bukan=bukan
    )

@app.route("/laporan/<int:laporan_id>")
def detail(laporan_id):

    response = requests.get(
        f"{API_URL}/laporan/{laporan_id}"
    )

    if response.status_code != 200:
        abort(404)

    laporan = response.json()

    return render_template(
        "detail.html",
        laporan=laporan
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