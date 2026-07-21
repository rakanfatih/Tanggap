from database.database import SessionLocal
from database.crud import simpan_laporan

db = SessionLocal()

laporan = simpan_laporan(
    db,
    {
        "pesan": "Rumah saya kebanjiran",
        "latitude": -6.2,
        "longitude": 106.8,
        "intent": "lapor_darurat",
        "disaster_type": "banjir",
        "confidence": 1.0,
        "validation_score": 100,
        "action": "escalate",
        "kategori_laporan": "insiden terverifikasi",
        "eskalasi_posko": True,
        "final_response": "Laporan diterima"
    }
)

print(laporan.id)