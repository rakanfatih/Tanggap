import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from graph_workflow import app as langgraph_app
from sqlalchemy.orm import Session
from fastapi import Depends
from database.database import get_db
from database.crud import simpan_laporan, get_all_laporan, get_laporan_by_id, update_status
from fastapi.middleware.cors import CORSMiddleware

# FastAPI  
app = FastAPI(
    title="Tanggap Multi-Agent API",
    description="Backend API Sistem Koordinasi Bencana Banjir berbasis Multi-Agent",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5000",
        "http://localhost:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# request model 
class LaporanRequest(BaseModel):

    user_message: str = Field(
        ...,
        description="Pesan yang dikirim warga."
    )

    lat: Optional[float] = Field(
        default=0.0,
        description="Latitude GPS."
    )

    lon: Optional[float] = Field(
        default=0.0,
        description="Longitude GPS."
    )

# response model
class LaporanResponse(BaseModel):

    intent: str
    disaster_type: str
    confidence: float
    action: str
    final_response: str
    eskalasi_posko: bool
    kategori_laporan: str

# dashboard model
class DashboardLaporan(BaseModel):

    id: int
    waktu: str
    pesan: str
    latitude: float
    longitude: float
    intent: str
    disaster_type: str
    confidence: float
    validation_score: int
    action: str
    kategori_laporan: str
    eskalasi_posko: bool
    final_response: str
    status: str

# update status mode
class UpdateStatusRequest(BaseModel):
    status: str

# endpoint
@app.post(
    "/api/lapor",
    response_model=LaporanResponse
)
async def proses_laporan(
    payload: LaporanRequest,
    db: Session = Depends(get_db)
):

    print("\n===================================")
    print("[FASTAPI]")
    print("===================================")

    print(f"Pesan      : {payload.user_message}")
    print(f"Latitude   : {payload.lat}")
    print(f"Longitude  : {payload.lon}")

    try:

        input_state = {
            "user_message": payload.user_message,
            "lat": payload.lat,
            "lon": payload.lon
        }

        hasil = langgraph_app.invoke(
            input_state
        )

        print("\n========== HASIL GRAPH ==========")

        print(f"Intent          : {hasil.get('intent')}")
        print(f"Disaster Type   : {hasil.get('disaster_type')}")
        print(f"Confidence      : {hasil.get('confidence')}")
        print(f"Action          : {hasil.get('action')}")
        print(f"Kategori        : {hasil.get('kategori_laporan')}")
        print(f"Eskalasi        : {hasil.get('eskalasi_posko')}")

        print("=================================\n")

        # simpan to database
        print("\n[MENYIMPAN KE DATABASE]")

        simpan_laporan(
            db=db,
            data={
                "pesan": payload.user_message,
                "latitude": payload.lat,
                "longitude": payload.lon,

                "intent": hasil.get(
                    "intent",
                    "lainnya"
                ),

                "disaster_type": hasil.get(
                    "disaster_type",
                    "lainnya"
                ),

                "confidence": hasil.get(
                    "confidence",
                    0.0
                ),

                "validation_score": hasil.get(
                    "validation_score",
                    0
                ),

                "action": hasil.get(
                    "action",
                    "reject"
                ),

                "kategori_laporan": hasil.get(
                    "kategori_laporan",
                    "bukan laporan"
                ),

                "eskalasi_posko": hasil.get(
                    "eskalasi_posko",
                    False
                ),

                "final_response": hasil.get(
                    "final_response",
                    "Terjadi kesalahan."
                )

            }
        )
        print("[DATABASE] Berhasil disimpan")

        return LaporanResponse(

            intent=hasil.get(
                "intent",
                "lainnya"
            ),

            disaster_type=hasil.get(
                "disaster_type",
                "lainnya"
            ),

            confidence=hasil.get(
                "confidence",
                0.0
            ),

            action=hasil.get(
                "action",
                "reject"
            ),

            final_response=hasil.get(
                "final_response",
                "Terjadi kesalahan."
            ),

            eskalasi_posko=hasil.get(
                "eskalasi_posko",
                False
            ),

            kategori_laporan=hasil.get(
                "kategori_laporan",
                "bukan laporan"
            )

        )

    except Exception as e:

        print("\n========== ERROR ==========")
        print(str(e))
        print("===========================\n")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get(
    "/api/laporan",
    response_model=list[DashboardLaporan]
)
def api_get_laporan(
    db: Session = Depends(get_db)
):

    laporan = get_all_laporan(db)
    hasil = []

    for item in laporan:
        hasil.append(
            DashboardLaporan(
                id=item.id,
                waktu=str(item.waktu),
                pesan=item.pesan,
                latitude=item.latitude,
                longitude=item.longitude,
                intent=item.intent,
                disaster_type=item.disaster_type,
                confidence=item.confidence,
                validation_score=item.validation_score,
                action=item.action,
                kategori_laporan=item.kategori_laporan,
                eskalasi_posko=item.eskalasi_posko,
                final_response=item.final_response,
                status=item.status
            )
        )

    return hasil


@app.get(
    "/api/laporan/{laporan_id}",
    response_model=DashboardLaporan
)
def api_get_laporan_by_id(
    laporan_id: int,
    db: Session = Depends(get_db)
):

    laporan = get_laporan_by_id(
        db,
        laporan_id
    )

    if laporan is None:
        raise HTTPException(
            status_code=404,
            detail="Laporan tidak ditemukan."
        )

    return DashboardLaporan(
        id=laporan.id,
        waktu=str(laporan.waktu),
        pesan=laporan.pesan,
        latitude=laporan.latitude,
        longitude=laporan.longitude,
        intent=laporan.intent,
        disaster_type=laporan.disaster_type,
        confidence=laporan.confidence,
        validation_score=laporan.validation_score,
        action=laporan.action,
        kategori_laporan=laporan.kategori_laporan,
        eskalasi_posko=laporan.eskalasi_posko,
        final_response=laporan.final_response,
        status=laporan.status
    )

@app.put("/api/laporan/{laporan_id}/status")
def api_update_status(
    laporan_id: int,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db)
):

    laporan = update_status(
        db,
        laporan_id,
        payload.status
    )

    if laporan is None:
        raise HTTPException(
            status_code=404,
            detail="Laporan tidak ditemukan."
        )

    return {
        "message": "Status berhasil diperbarui.",
        "status": laporan.status
    }

@app.get("/api/map")
async def get_map_data(
    db: Session = Depends(get_db)
):

    laporan = get_all_laporan(db)
    hasil = []

    for item in laporan:
        hasil.append(
            {
                "id": item.id,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "pesan": item.pesan,
                "kategori": item.kategori_laporan,
                "status": item.status
            }
        )

    return hasil

# run
if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )