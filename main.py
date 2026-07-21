import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from graph_workflow import app as langgraph_app

# FastAPI  
app = FastAPI(
    title="Tanggap Multi-Agent API",
    description="Backend API Sistem Koordinasi Bencana Banjir berbasis Multi-Agent",
    version="2.0"
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

# endpoint
@app.post(
    "/api/lapor",
    response_model=LaporanResponse
)

async def proses_laporan(
    payload: LaporanRequest
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

# run
if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )