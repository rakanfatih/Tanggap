from sqlalchemy.orm import Session
from database.models import Laporan


def simpan_laporan(
    db: Session,
    data: dict
):

    laporan = Laporan(
        session_id=data.get("session_id", "default_session"),
        processing_time=data.get("processing_time", 0.0),
        pesan=data["pesan"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        image_path=data.get("image_path"),
        intent=data["intent"],
        disaster_type=data["disaster_type"],
        confidence=data["confidence"],
        validation_score=data["validation_score"],
        action=data["action"],
        kategori_laporan=data["kategori_laporan"],
        eskalasi_posko=data["eskalasi_posko"],
        final_response=data["final_response"],
        vision_score=data.get("vision_score"),
        vision_result=data.get("vision_result")
    )

    db.add(laporan)
    db.commit()
    db.refresh(laporan)

    return laporan

def get_chat_history(
        db: Session, 
        session_id: str, 
        limit: int = 5
):
    
    histori = (
        db.query(Laporan)
        .filter(Laporan.session_id == session_id)
        .order_by(Laporan.waktu.asc())
        .limit(limit)
        .all()
    )
    
    chat_history = ""
    for h in histori:
        chat_history += f"Warga: {h.pesan}\n"
        chat_history += f"GARDA: {h.final_response}\n\n"
        
    return chat_history

def get_all_laporan(
    db: Session
):

    return (
        db.query(Laporan)
        .order_by(Laporan.waktu.desc())
        .all()
    )


def get_laporan_by_id(
    db: Session,
    laporan_id: int
):

    return (
        db.query(Laporan)
        .filter(Laporan.id == laporan_id)
        .first()
    )

def update_status(
    db: Session,
    laporan_id: int,
    status: str
):

    laporan = get_laporan_by_id(
        db,
        laporan_id
    )

    if laporan is None:
        return None

    laporan.status = status

    db.commit()
    db.refresh(laporan)

    return laporan