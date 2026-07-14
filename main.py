import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from graph_workflow import app as langgraph_app

#inisialisasi
app = FastAPI(
    title="API sistem koordinasi bencana banjir multi-agent",
    description="backend API berbasis fastAPI untuk menghubungkan Android dengan LLM"
)

#request
class LaporanRequest(BaseModel):
    user_message: str = Field(..., description="pesan dari warga yang dikirim melalui aplikasi Android")
    lat: Optional[float] = Field(default=0.0, description="opsional, koordinat GPS latitude dari lokasi warga")
    lon: Optional[float] = Field(default=0.0, description="opsional, koordinat GPS longtitude dari lokasi warga")

#response
class LaporanResponse(BaseModel):
    intent: str = Field(..., description="hasil klasifikasi intent dari agen router: 'lapor_darurat', 'tanya_info', atau 'lainnya'")
    final_response: str = Field(..., description="pesan balasan yang akan diteruskan ke warga")
    eskalasi_posko: bool = Field(..., description="true jika laporan darurat butuh penanganan tim posko, false jika hanya pertanyaan info atau spam")
    kategori_laporan: str = Field(..., description="pilih salah satu: 'insiden terverifikasi', 'perlu tinjauan', atau 'bukan laporan'")

#post endpoint
@app.post("/api/lapor", response_model=LaporanResponse)
async def proses_laporan_warga(payload: LaporanRequest):
    print("\n" + "="*40)
    print(f"[API] menerima request masuk dari aplikasi Android...")
    print(f"Pesan: {payload.user_message}")
    print(f"Lokasi: [{payload.lat}, {payload.lon}]")
    print("="*40)

    try:
        input_state = {
            "user_message": payload.user_message,
            "lat": payload.lat,
            "lon": payload.lon
        }
    
        hasil_workflow = langgraph_app.invoke(input_state)

        print("[API] Pemrosesan Multi-Agent selesai. Mengirimkan response balik...")

        return LaporanResponse(
            intent=hasil_workflow.get("intent", "info"),
            final_response=hasil_workflow.get("final_response", "Sistem sedang memproses..."),
            eskalasi_posko=hasil_workflow.get("eskalasi_posko", False),
            kategori_laporan=hasil_workflow.get("kategori_laporan", "pencarian informasi")
    )

    except Exception as e:
        print(f"[API ERROR] terjadi kesalahan saat memproses laporan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
#local server
if __name__ == "__main__":
    # host 0.0.0.0, android 1 wi-fi
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)