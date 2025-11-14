import os
import time
from sqlalchemy.orm import Session
from models import Landmark, LandmarkImage
from models import User

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# existing landmarks folder in repository (plural 'landmarks' as in workspace)
LANDMARKS_DIR = os.path.join(BASE_DIR, "landmarks")


def get_landmarks(db: Session):
    return db.query(Landmark).order_by(Landmark.name).all()


def get_landmark(db: Session, landmark_id: int):
    return db.query(Landmark).filter(Landmark.id == landmark_id).first()


def get_landmark_by_name(db: Session, name: str):
    return db.query(Landmark).filter(Landmark.name == name).first()


def create_landmark(db: Session, name: str, description: str = None):
    lm = Landmark(name=name, description=description)
    db.add(lm)
    db.commit()
    db.refresh(lm)
    return lm


def ensure_landmark_folder(name: str):
    folder = os.path.join(LANDMARKS_DIR, name)
    os.makedirs(folder, exist_ok=True)
    return folder


def save_landmark_image(db: Session, landmark: Landmark, filename: str):
    # legacy wrapper kept for compatibility; image_uuid should be provided in new usage
    from uuid import uuid4
    image_uuid = str(uuid4())
    img = LandmarkImage(landmark_id=landmark.id, filename=filename, image_uuid=image_uuid)
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str):
    # import locally to avoid circular imports (auth imports crud)
    from auth import get_password_hash
    hashed = get_password_hash(password)
    user = User(username=username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_uploaded_file_to_landmark(landmark_name: str, upload_file) -> tuple:
    folder = ensure_landmark_folder(landmark_name)
    ts = int(time.time())
    safe_name = f"{ts}_{os.path.basename(upload_file.filename)}"
    dest_path = os.path.join(folder, safe_name)
    # write file bytes
    upload_file.file.seek(0)
    with open(dest_path, "wb") as f:
        f.write(upload_file.file.read())
    # return filename and filesystem path
    return safe_name, dest_path
