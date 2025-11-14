from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base


class Landmark(Base):
    __tablename__ = "landmarks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    images = relationship("LandmarkImage", back_populates="landmark", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class LandmarkImage(Base):
    __tablename__ = "landmark_images"
    id = Column(Integer, primary_key=True, index=True)
    landmark_id = Column(Integer, ForeignKey("landmarks.id"), nullable=False)
    filename = Column(String, nullable=False)
    image_uuid = Column(String, unique=True, index=True, nullable=False)
    uploader_username = Column(String, nullable=True)
    embedding_path = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    landmark = relationship("Landmark", back_populates="images")
