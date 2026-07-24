from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from datetime import datetime
from database.database import Base


class Laporan(Base):

    __tablename__ = "laporan"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    waktu = Column(
        DateTime,
        default=datetime.utcnow
    )

    pesan = Column(
        String
    )

    latitude = Column(
        Float
    )

    longitude = Column(
        Float
    )

    intent = Column(
        String
    )

    disaster_type = Column(
        String
    )

    confidence = Column(
        Float
    )

    validation_score = Column(
        Integer
    )

    action = Column(
        String
    )

    kategori_laporan = Column(
        String
    )

    eskalasi_posko = Column(
        Boolean
    )

    final_response = Column(
        String
    )

    # vision
    image_path = Column(
        String,
        nullable=True
    )

    vision_score = Column(
        Float,
        nullable=True
    )

    vision_result = Column(
        String,
        nullable=True
    )

    status = Column(
        String,
        default="Menunggu"
    )