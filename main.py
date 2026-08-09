import os
import uuid
import shutil
import uvicorn
import time
import json
from dotenv import load_dotenv
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from graph_workflow import app as langgraph_app
from database.database import get_db
from database.models import Laporan
from database.crud import (
    simpan_laporan, 
    get_all_laporan, 
    get_laporan_by_id, 
    update_status, 
    get_chat_history,
    update_kategori_laporan
)

load_dotenv(override=True)

# batasi IP address
limiter = Limiter(key_func=get_remote_address)

# FastAPI  
app = FastAPI(
    title="Tanggap Multi-Agent API",
    description="Backend API Sistem Koordinasi Bencana Banjir berbasis Multi-Agent",
    version="2.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

os.makedirs("assets_edukasi", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets_edukasi"), name="assets")

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://127.0.0.1:5000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        DASHBOARD_URL,
        "http://localhost:5000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# request & response model
class LaporanRequest(BaseModel):
    session_id: str = Field(default="default_session", description="ID unik untuk setiap user/perangkat")
    user_message: str = Field(..., description="Pesan yang dikirim warga.")
    lat: Optional[float] = Field(default=0.0, description="Latitude GPS.")
    lon: Optional[float] = Field(default=0.0, description="Longitude GPS.")
    image_path: Optional[str] = Field(default=None, description="Path gambar.")

class LaporanResponse(BaseModel):
    intent: str
    disaster_type: str
    confidence: float
    action: str
    final_response: str
    eskalasi_posko: bool
    kategori_laporan: str
    processing_time: float

class DashboardLaporan(BaseModel):
    id: int
    waktu: str
    pesan: str
    latitude: float
    longitude: float
    alamat: Optional[str] = None
    image_path: Optional[str] = None
    vision_score: Optional[float] = None
    vision_result: Optional[str] = None
    vision_image_path: Optional[str] = None
    intent: str
    disaster_type: str
    confidence: float
    validation_score: int
    action: str
    kategori_laporan: str
    eskalasi_posko: bool
    final_response: str
    status: str

class UpdateStatusRequest(BaseModel):
    status: str

class UpdateKategoriRequest(BaseModel):
    kategori: str

class EdukasiItem(BaseModel):
    id: str
    judul: str
    deskripsi: str
    thumbnail: str
    tipe_konten: str
    durasi: str
    file_url: str


# API endpoints
@app.post("/api/lapor", response_model=LaporanResponse)
@limiter.limit("5/minute")
async def proses_laporan(
    payload: LaporanRequest,
    db: Session = Depends(get_db)
):
    try:
        riwayat = get_chat_history(db, payload.session_id)

        input_state = {
            "user_message": payload.user_message,
            "lat": payload.lat,
            "lon": payload.lon,
            "image_path": payload.image_path,
            "chat_history": riwayat
        }

        start_time = time.time()
        hasil = langgraph_app.invoke(input_state)
        end_time = time.time()
        latensi = round(end_time - start_time, 2)

        intent_terdeteksi = hasil.get("intent", "lainnya") 
        kategori_terdeteksi = hasil.get("kategori_laporan", "bukan laporan")

        if intent_terdeteksi != "lapor_darurat" or kategori_terdeteksi == "bukan laporan":
            return LaporanResponse(
                intent=intent_terdeteksi,
                disaster_type=hasil.get("disaster_type", "lainnya"),
                confidence=hasil.get("confidence", 0.0),
                action=hasil.get("action", "reject"),
                final_response=hasil.get("final_response", "Terjadi kesalahan."),
                eskalasi_posko=False,
                kategori_laporan=hasil.get("kategori_laporan", "bukan laporan"),
                processing_time=latensi
            )

        objek_terdeteksi = hasil.get("visible_objects", [])
        vision_detail = {
            "severity": hasil.get("severity", "-"),
            "water_cm": hasil.get("estimated_water_cm", 0),
            "water_percentage": hasil.get("water_percentage", 0),
            "objects": ", ".join(objek_terdeteksi) if objek_terdeteksi else "Tidak ada",
            "reason": hasil.get("vision_reason", "")
        }

        simpan_laporan(
            db=db,
            data={
                "session_id": payload.session_id, 
                "processing_time": latensi,
                "pesan": payload.user_message,
                "latitude": payload.lat,
                "longitude": payload.lon,
                "alamat_lengkap": hasil.get("alamat_lengkap"),
                "image_path": payload.image_path,
                "intent": hasil.get("intent", "lainnya"),
                "disaster_type": hasil.get("disaster_type", "lainnya"),
                "confidence": hasil.get("confidence", 0.0),
                "validation_score": hasil.get("validation_score", 0),
                "action": hasil.get("action", "reject"),
                "kategori_laporan": hasil.get("kategori_laporan", "bukan laporan"),
                "eskalasi_posko": hasil.get("eskalasi_posko", False),
                "final_response": hasil.get("final_response", "Terjadi kesalahan."), 
                "vision_score": hasil.get("vision_confidence"), 
                "vision_result": json.dumps(vision_detail),
                "vision_image_path": hasil.get("vision_image_path")
            }
        )

        return LaporanResponse(
            intent=hasil.get("intent", "lainnya"),
            disaster_type=hasil.get("disaster_type", "lainnya"),
            confidence=hasil.get("confidence", 0.0),
            action=hasil.get("action", "reject"),
            final_response=hasil.get("final_response", "Terjadi kesalahan."),
            eskalasi_posko=hasil.get("eskalasi_posko", False),
            kategori_laporan=hasil.get("kategori_laporan", "bukan laporan"),
            processing_time=latensi
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan pada server: {str(e)}"
        )

@app.get("/api/laporan", response_model=list[DashboardLaporan])
def api_get_laporan(db: Session = Depends(get_db)):
    laporan = get_all_laporan(db)
    hasil = []

    for item in laporan:
        intent_val = item.router.intent if item.router else "lainnya"

        if intent_val == "tanya_info":
            continue

        hasil.append(
            DashboardLaporan(
                id=item.id,
                waktu=item.waktu.strftime("%d-%m-%Y %H:%M"),
                pesan=item.pesan,
                latitude=item.latitude,
                longitude=item.longitude,
                alamat=item.alamat or "Lokasi tidak diketahui",
                image_path=item.image_path,
                vision_score=item.vision.vision_score if item.vision else None,
                vision_result=item.vision.vision_result if item.vision else None,
                vision_image_path=item.vision.vision_image_path if item.vision else None,
                intent=intent_val,
                disaster_type=item.router.disaster_type if item.router else "lainnya",
                confidence=item.router.confidence if item.router else 0.0,
                validation_score=item.validator.validation_score if item.validator else 0,
                action=item.decision.action if item.decision else "reject",
                kategori_laporan=item.decision.kategori_laporan if item.decision else "bukan laporan",
                eskalasi_posko=item.decision.eskalasi_posko if item.decision else False,
                final_response=item.executor.final_response if item.executor else "Tidak ada respons.",
                status=item.status
            )
        )

    return hasil

@app.get("/api/laporan/{laporan_id}", response_model=DashboardLaporan)
def api_get_laporan_by_id(laporan_id: int, db: Session = Depends(get_db)):
    item = get_laporan_by_id(db, laporan_id)

    if item is None:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan.")

    return DashboardLaporan(
        id=item.id,
        waktu=item.waktu.strftime("%d-%m-%Y %H:%M"),
        pesan=item.pesan,
        latitude=item.latitude,
        longitude=item.longitude,
        image_path=item.image_path,
        vision_score=item.vision.vision_score if item.vision else None,
        vision_result=item.vision.vision_result if item.vision else None,
        vision_image_path=item.vision.vision_image_path if item.vision else None,
        intent=item.router.intent if item.router else "lainnya",
        disaster_type=item.router.disaster_type if item.router else "lainnya",
        confidence=item.router.confidence if item.router else 0.0,
        validation_score=item.validator.validation_score if item.validator else 0,
        action=item.decision.action if item.decision else "reject",
        kategori_laporan=item.decision.kategori_laporan if item.decision else "bukan laporan",
        eskalasi_posko=item.decision.eskalasi_posko if item.decision else False,
        final_response=item.executor.final_response if item.executor else "Tidak ada respons.",
        status=item.status
    )

@app.get("/api/riwayat/{session_id}")
def api_get_riwayat_user(session_id: str, db: Session = Depends(get_db)):
    histori = (
        db.query(Laporan)
        .filter(Laporan.session_id == session_id)
        .order_by(Laporan.waktu.desc())
        .all()
    )
    
    hasil = []
    for item in histori:
        intent_val = item.router.intent if item.router else "lainnya"
        if intent_val == "tanya_info":
            continue
            
        hasil.append({
            "id": item.id,
            "waktu": item.waktu.strftime("%d-%m-%Y %H:%M"),
            "pesan": item.pesan,
            "status": item.status,
            "kategori_laporan": item.decision.kategori_laporan if item.decision else "bukan laporan",
            "final_response": item.executor.final_response if item.executor else "Sedang diproses."
        })
        
    return hasil

@app.put("/api/laporan/{laporan_id}/status")
def api_update_status(
    laporan_id: int, 
    payload: UpdateStatusRequest, 
    db: Session = Depends(get_db)
):
    laporan = update_status(db, laporan_id, payload.status)

    if laporan is None:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan.")

    return {
        "message": "Status berhasil diperbarui.",
        "status": laporan.status
    }

@app.get("/api/map")
async def get_map_data(db: Session = Depends(get_db)):
    laporan = get_all_laporan(db)
    hasil = []

    for item in laporan:
        intent_val = item.router.intent if item.router else "lainnya"
        if intent_val == "tanya_info":
            continue

        hasil.append(
            {
                "id": item.id,
                "waktu": item.waktu.strftime("%d-%m-%Y %H:%M"),
                "latitude": item.latitude,
                "longitude": item.longitude,
                "alamat": item.alamat or "Lokasi tidak diketahui",
                "pesan": item.pesan,
                "kategori": item.decision.kategori_laporan if item.decision else "bukan laporan",
                "status": item.status
            }
        )

    return hasil

@app.post("/upload-image")
async def upload_image(image: UploadFile = File(...)):
    ext = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return {
        "filename": filename,
        "path": filepath
    }

SERVER_URL = os.getenv("SERVER_URL", "http://192.168.1.10:8000")
DATA_EDUKASI = []

try:
    with open("edukasi.json", "r", encoding="utf-8") as file:
        RAW_DATA_EDUKASI = json.load(file)
        
        for item in RAW_DATA_EDUKASI:
            is_external_link = item["file"].startswith("http")
            final_file_url = item["file"] if is_external_link else f"{SERVER_URL}/assets/{item['file']}"
            
            DATA_EDUKASI.append(
                EdukasiItem(
                    id=item["id"],
                    judul=item["judul"],
                    deskripsi=item["deskripsi"],
                    thumbnail=f"{SERVER_URL}/assets/{item['gambar']}",
                    tipe_konten=item["tipe"],
                    durasi=item["durasi"],
                    file_url=final_file_url
                )
            )
except Exception:
    pass

@app.get("/api/edukasi", response_model=list[EdukasiItem])
def get_semua_edukasi(tipe: Optional[str] = None):
    hasil = DATA_EDUKASI
    
    if tipe and tipe.lower() != "semua":
        hasil = [
            item for item in hasil 
            if item.tipe_konten.lower() == tipe.lower()
        ]
        
    return hasil

@app.put("/api/laporan/{laporan_id}/kategori")
def api_update_kategori(laporan_id: int, payload: UpdateKategoriRequest, db: Session = Depends(get_db)):
    laporan = update_kategori_laporan(db, laporan_id, payload.kategori)

    if laporan is None:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan.")

    return {
        "message": "Kategori berhasil diperbarui.",
        "kategori": laporan.decision.kategori_laporan
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False 
    )