from flask import Flask, render_template, abort
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from database.database import SessionLocal
from database.crud import(
    get_all_laporan,
    get_laporan_by_id
)
    
app = Flask(__name__)

@app.route("/")
def index():

    db = SessionLocal()

    try:
        laporan = get_all_laporan(db)
        total = len(laporan)

        terverifikasi = sum(
            1
            for x in laporan
            if x.kategori_laporan == "insiden terverifikasi"
        )

        review = sum(
            1
            for x in laporan
            if x.kategori_laporan == "perlu tinjauan"
        )

        bukan = sum(
            1
            for x in laporan
            if x.kategori_laporan == "bukan laporan"
        )

    finally:
        db.close()

    return render_template(
        "index.html",
        laporan=laporan,
        total=total,
        terverifikasi=terverifikasi,
        review=review,
        bukan=bukan
    )

@app.route("/laporan/<int:laporan_id>")
def detail_laporan(laporan_id):

    db = SessionLocal()

    try:
        laporan = get_laporan_by_id(
            db,
            laporan_id
        )

        if laporan is None:
            abort(404)

    finally:
        db.close()

    return render_template(
        "detail.html",
        laporan=laporan
    )

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )