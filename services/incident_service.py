from sqlalchemy.orm import Session

from database.models import Laporan


def save_incident(db: Session, state: dict):

    laporan = Laporan(
        pesan=state["user_message"],
        latitude=state["lat"],
        longitude=state["lon"],
        intent=state["intent"],
        disaster_type=state["disaster_type"],
        confidence=state["confidence"],
        validation_score=state["validation_score"],
        action=state["action"],
        kategori_laporan=state["kategori_laporan"],
        eskalasi_posko=state["eskalasi_posko"],
        final_response=state["final_response"],
        image_path=state["image_path"],
        vision_score=state["vision_confidence"],
        vision_result=state["severity"]
    )

    db.add(laporan)

    db.commit()

    db.refresh(laporan)

    return laporan