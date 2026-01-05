import os
import time

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Landmark, LandmarkImage, User
from utils import normalize_name

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LANDMARKS_DIR = os.path.join(BASE_DIR, "landmarks")


def get_landmarks(db: Session):
    return db.query(Landmark).order_by(Landmark.name).all()


def get_landmark(db: Session, landmark_id: int):
    return db.query(Landmark).filter(Landmark.id == landmark_id).first()


def get_landmark_by_name(db: Session, name: str):
    canon = normalize_name(name)
    landmark = db.query(Landmark).filter(func.lower(Landmark.name) == canon.lower()).first()
    # If found but name doesn't match exactly, update it to normalized version
    if landmark and landmark.name != canon:
        print(f"🔧 get_landmark_by_name: Fixing casing '{landmark.name}' -> '{canon}'")
        landmark.name = canon
        db.commit()
        db.refresh(landmark)
    return landmark


# ✅ REQUIRED FOR feedback/meta
def get_landmark_image(db: Session, image_id: int):
    return db.query(LandmarkImage).filter(LandmarkImage.id == image_id).first()


def create_landmark(db: Session, name: str, description: str = None):
    # Always normalize the name to ensure consistency (Title_Case_With_Underscores)
    normalized_name = normalize_name(name)
    if name != normalized_name:
        print(f"⚠️  create_landmark: Normalized '{name}' -> '{normalized_name}'")
    lm = Landmark(name=normalized_name, description=description)
    db.add(lm)
    db.commit()
    db.refresh(lm)
    print(f"✅ create_landmark: Created landmark with name '{lm.name}'")
    return lm


def ensure_landmark_folder(name: str):
    folder = os.path.join(LANDMARKS_DIR, name)
    os.makedirs(folder, exist_ok=True)
    return folder


def save_landmark_image(db: Session, landmark: Landmark, filename: str):
    from uuid import uuid4

    image_uuid = str(uuid4())
    img = LandmarkImage(
        landmark_id=landmark.id, filename=filename, image_uuid=image_uuid
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


def save_uploaded_file_to_landmark(landmark_name: str, upload_file) -> tuple:
    folder = ensure_landmark_folder(landmark_name)
    ts = int(time.time())
    safe_name = f"{ts}_{os.path.basename(upload_file.filename)}"
    dest_path = os.path.join(folder, safe_name)
    upload_file.file.seek(0)

    with open(dest_path, "wb") as f:
        f.write(upload_file.file.read())

    return safe_name, dest_path
