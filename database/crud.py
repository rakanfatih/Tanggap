from sqlalchemy.orm import Session
from database.models import Laporan, Router, Validator, Decision, Vision, Executor


def simpan_laporan(db: Session, data: dict):
    status_awal = "Diproses" if data.get("kategori_laporan") == "insiden terverifikasi" else "Menunggu"

    laporan = Laporan(
        session_id=data.get("session_id", "default_session"),
        processing_time=data.get("processing_time", 0.0),
        pesan=data["pesan"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        alamat=data.get("alamat_lengkap"),
        image_path=data.get("image_path"),
        status=status_awal
    )

    db.add(laporan)
    db.flush() 

    # simpan data router
    router = Router(
        laporan_id=laporan.id,
        intent=data["intent"],
        disaster_type=data["disaster_type"],
        confidence=data["confidence"]
    )
    db.add(router)

    # simpan data validator
    validator = Validator(
        laporan_id=laporan.id,
        validation_score=data["validation_score"]
    )
    db.add(validator)

    # simpan data decision
    decision = Decision(
        laporan_id=laporan.id,
        action=data["action"],
        kategori_laporan=data["kategori_laporan"],
        eskalasi_posko=data["eskalasi_posko"],
    )
    db.add(decision)

    # simpan data executor
    executor = Executor(
        laporan_id=laporan.id,
        final_response=data["final_response"]
    )
    db.add(executor)

    # simpan data vision
    vision = Vision(
        laporan_id=laporan.id,
        vision_score=data.get("vision_score"),
        vision_result=data.get("vision_result"),
        vision_image_path=data.get("vision_image_path")
    )
    db.add(vision)

    db.commit()
    db.refresh(laporan)

    return laporan


def get_chat_history(db: Session, session_id: str, limit: int = 5):
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
        if h.executor:
            chat_history += f"GARDA: {h.executor.final_response}\n\n"
        else:
            chat_history += "GARDA: \n\n"
        
    return chat_history


def get_all_laporan(db: Session):
    return (
        db.query(Laporan)
        .order_by(Laporan.waktu.desc())
        .all()
    )


def get_laporan_by_id(db: Session, laporan_id: int):
    return (
        db.query(Laporan)
        .filter(Laporan.id == laporan_id)
        .first()
    )


def update_status(db: Session, laporan_id: int, status: str):
    laporan = get_laporan_by_id(db, laporan_id)

    if laporan is None:
        return None

    laporan.status = status

    db.commit()
    db.refresh(laporan)

    return laporan


def update_kategori_laporan(db: Session, laporan_id: int, kategori: str):
    laporan = get_laporan_by_id(db, laporan_id)

    if laporan and laporan.decision:
        laporan.decision.kategori_laporan = kategori
        
        if kategori == "insiden terverifikasi" and laporan.status == "Menunggu":
            laporan.status = "Diproses"
            
        db.commit()
        db.refresh(laporan)

    return laporan