import os
import shutil
from datetime import datetime
from typing import Tuple

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def normalize_name(name: str) -> str:
    """Normalize landmark name to TitleCase with underscores."""
    if not name:
        return "Unknown"

    words = name.strip().split()
    return "_".join(w.capitalize() for w in words)


def ensure_folder(path: str):
    """Create folder (and parents) if missing."""
    os.makedirs(path, exist_ok=True)


def is_allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def save_uploaded_image(file, folder: str) -> str:
    """Save uploaded file into folder, return saved filepath.

    The filename uses a timestamp to avoid collisions.
    """
    ensure_folder(folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{os.path.basename(file.filename)}"
    filepath = os.path.join(folder, filename)
    # Use shutil.copyfileobj to stream from UploadFile.file
    file.file.seek(0)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return filepath


def move_image(image_path: str, new_folder: str) -> str:
    """Move image to new folder, return new path."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    ensure_folder(new_folder)
    new_path = os.path.join(new_folder, os.path.basename(image_path))
    shutil.move(image_path, new_path)
    return new_path
