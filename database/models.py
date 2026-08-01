from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

# laporan
class Laporan(Base):
    __tablename__ = "laporan"

    id = Column(Integer, primary_key=True, index=True)
    waktu = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String, default="default_session")
    processing_time = Column(Float, default=0.0)
    pesan = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    alamat = Column(String, nullable=True, default="Lokasi tidak diketahui")
    image_path = Column(String, nullable=True)
    status = Column(String, default="Menunggu")

    # relasi
    router = relationship("Router", back_populates="laporan", uselist=False, cascade="all, delete-orphan")
    validator = relationship("Validator", back_populates="laporan", uselist=False, cascade="all, delete-orphan")
    decision = relationship("Decision", back_populates="laporan", uselist=False, cascade="all, delete-orphan")
    vision = relationship("Vision", back_populates="laporan", uselist=False, cascade="all, delete-orphan")

# router
class Router(Base):
    __tablename__ = "router"

    id = Column(Integer, primary_key=True, index=True)
    laporan_id = Column(Integer, ForeignKey("laporan.id", ondelete="CASCADE"))
    intent = Column(String)
    disaster_type = Column(String)
    confidence = Column(Float)

    laporan = relationship("Laporan", back_populates="router")

# validator
class Validator(Base):
    __tablename__ = "validator"

    id = Column(Integer, primary_key=True, index=True)
    laporan_id = Column(Integer, ForeignKey("laporan.id", ondelete="CASCADE"))
    validation_score = Column(Integer)

    laporan = relationship("Laporan", back_populates="validator")

# decision
class Decision(Base):
    __tablename__ = "decision"

    id = Column(Integer, primary_key=True, index=True)
    laporan_id = Column(Integer, ForeignKey("laporan.id", ondelete="CASCADE"))
    action = Column(String)
    kategori_laporan = Column(String)
    eskalasi_posko = Column(Boolean)
    final_response = Column(String)

    laporan = relationship("Laporan", back_populates="decision")

# vision
class Vision(Base):
    __tablename__ = "vision"

    id = Column(Integer, primary_key=True, index=True)
    laporan_id = Column(Integer, ForeignKey("laporan.id", ondelete="CASCADE"))
    vision_score = Column(Float, nullable=True)
    vision_result = Column(String, nullable=True)
    vision_image_path = Column(String, nullable=True)

    laporan = relationship("Laporan", back_populates="vision")