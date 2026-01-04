"""
GeoGenie — FastAPI Backend
Handles:
- Landmark recognition (GPS + CLIP)
- Live FAISS search engine
- Feedback upload with auto DB & FAISS update
- Chat about place (HTML output)
- Landmark management
"""

import io
import os
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session

import crud
import models
from ai_client import call_gemini

# Local imports
from db import Base, SessionLocal, engine
from embed_generator import get_embedder
from exif_utils import extract_gps_from_bytes
from geocode import get_geocoder
from search_image import get_search_engine
from utils import ensure_folder, is_allowed_file, move_image, normalize_name


# ---------------------------------------------------
# Proper DB dependency
# ---------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------
# FastAPI Init
# ---------------------------------------------------
app = FastAPI(title="GeoGenie API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# Pydantic Models
# ---------------------------------------------------
class RecognitionResponse(BaseModel):
    place_name: str
    confidence: float
    source: str
    coordinates: Optional[list] = None


class PlaceInfoResponse(BaseModel):
    name: str
    description: str
    summary: Optional[str] = None
    wikipedia_url: Optional[str] = None


# ---------------------------------------------------
# Startup Sync
# ---------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("Starting GeoGenie backend...")

    Base.metadata.create_all(bind=engine)

    # Ensure landmark folder exists and sync with DB
    base_landmarks = crud.LANDMARKS_DIR
    ensure_folder(base_landmarks)

    db = SessionLocal()
    try:
        for entry in os.listdir(base_landmarks):
            full = os.path.join(base_landmarks, entry)
            if os.path.isdir(full):
                if not crud.get_landmark_by_name(db, entry):
                    crud.create_landmark(db, entry)
    finally:
        db.close()

    print("\nRegistered Routes:")
    for r in app.routes:
        print(f"{r.path} -> {r.methods}")


# ---------------------------------------------------
# Root / Debug
# ---------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "service": "GeoGenie API"}


@app.get("/debug/routes")
async def debug_routes():
    return {
        "routes": [
            {"path": r.path, "methods": list(getattr(r, "methods", []))}
            for r in app.routes
        ]
    }


# ---------------------------------------------------
# Landmark Recognition
# ---------------------------------------------------
@app.post("/recognize", response_model=RecognitionResponse)
async def recognize_landmark(
    image: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
):
    try:
        img_bytes = await image.read()
        img_pil = Image.open(io.BytesIO(img_bytes))

        # GPS if provided or from EXIF
        gps = (
            (latitude, longitude)
            if latitude and longitude
            else extract_gps_from_bytes(img_bytes)
        )

        if gps:
            geo = get_geocoder()
            res = geo.reverse_geocode(gps[0], gps[1])
            if res and res.get("place_name"):
                return RecognitionResponse(
                    place_name=res["place_name"],
                    confidence=0.95,
                    source="gps",
                    coordinates=list(gps),
                )

        # Visual (CLIP + FAISS)
        embedder = get_embedder()
        search = get_search_engine()

        emb = embedder.generate_embedding(img_pil)
        best = search.get_best_match(emb, threshold=0.6)

        if best:
            return RecognitionResponse(
                place_name=best["place_name"],
                confidence=best["confidence"],
                source="visual",
                coordinates=list(gps) if gps else None,
            )

        return RecognitionResponse(
            place_name="Unknown",
            confidence=0.0,
            source="visual",
            coordinates=list(gps) if gps else None,
        )

    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------
# Landmarks — DB List
# ---------------------------------------------------
@app.get("/landmarks")
async def list_landmarks(db: Session = Depends(get_db)):
    return [{"id": lm.id, "name": lm.name} for lm in crud.get_landmarks(db)]


# ---------------------------------------------------
# Add Landmark
# ---------------------------------------------------
@app.post("/landmarks/add")
async def add_landmark(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        norm = normalize_name(name)
        existing = crud.get_landmark_by_name(db, norm)
        if existing:
            return {
                "status": "exists",
                "landmark": {"id": existing.id, "name": existing.name},
            }

        ensure_folder(os.path.join(crud.LANDMARKS_DIR, norm))
        landmark = crud.create_landmark(db, norm, description)

        return {
            "status": "created",
            "landmark": {
                "id": landmark.id,
                "name": landmark.name,
            },
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------
# List Folder-based Landmarks
# ---------------------------------------------------
@app.get("/landmarks/list")
async def list_landmark_folders():
    base = crud.LANDMARKS_DIR
    ensure_folder(base)

    entries = sorted(
        [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
    )
    if "unknown" not in entries:
        entries.append("unknown")

    return {"landmarks": entries}


# ---------------------------------------------------
# FEEDBACK UPLOAD (image + optional metadata)
# This ALWAYS saves the image, even for existing landmarks.
# ---------------------------------------------------
@app.post("/feedback/upload")
async def upload_feedback(
    landmark_id: Optional[int] = Form(None),
    landmark_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # ---------------------------
        # Resolve or create landmark
        # ---------------------------
        if landmark_id:
            landmark = crud.get_landmark(db, landmark_id)
            if not landmark:
                raise HTTPException(404, "❌ Landmark not found")
        else:
            norm = normalize_name(landmark_name) if landmark_name else "unknown"
            landmark = crud.get_landmark_by_name(db, norm)
            if not landmark:
                landmark = crud.create_landmark(db, norm, description)
                print(f"🆕 Created landmark: {landmark.name}")
            else:
                print(f"📍 Using existing landmark: {landmark.name}")

        # ---------------------------
        # ALWAYS save image
        # ---------------------------
        filename, saved_path = crud.save_uploaded_file_to_landmark(landmark.name, file)
        img_record = crud.save_landmark_image(db, landmark, filename)
        print(f"💾 Saved image '{filename}' under '{landmark.name}'")

        # ---------------------------
        # Parse coords
        # ---------------------------
        try:
            lat_val = float(latitude) if latitude not in (None, "", "null") else None
            lng_val = float(longitude) if longitude not in (None, "", "null") else None
        except Exception:
            lat_val = None
            lng_val = None

        # ---------------------------
        # Update FAISS
        # ---------------------------
        try:
            if landmark.name == "unknown":
                print("⏭ Skipping FAISS (unknown placeholder)")
            else:
                embedder = get_embedder()
                search = get_search_engine()

                pil_img = Image.open(saved_path).convert("RGB")
                emb = embedder.generate_embedding(pil_img)

                search.add_landmark(
                    embedding=emb,
                    place_name=landmark.name,
                    image_path=saved_path,
                )

                print(f"🧠 FAISS: added embedding for '{landmark.name}'")

        except Exception as e:
            print("⚠ FAISS embedding failed:", e)

        return {
            "status": "success",
            "landmark_id": landmark.id,
            "image_id": img_record.id,
            "filename": filename,
            "coordinates": [lat_val, lng_val] if (lat_val and lng_val) else None,
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------
# FEEDBACK META (metadata AFTER upload)
# Updates landmark association, moves file, re-embeds.
# ---------------------------------------------------
@app.post("/feedback/meta")
async def update_feedback_meta(
    image_id: int = Form(...),
    landmark_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        img = crud.get_landmark_image(db, image_id)
        if not img:
            raise HTTPException(404, "Image not found")

        current_landmark = crud.get_landmark(db, img.landmark_id)
        if not current_landmark:
            raise HTTPException(404, "Current landmark not found")

        # Determine target landmark
        if landmark_name:
            norm = normalize_name(landmark_name)
            print(f"🔍 Normalized '{landmark_name}' -> '{norm}'")
            new_landmark = crud.get_landmark_by_name(db, norm)
            if not new_landmark:
                new_landmark = crud.create_landmark(db, norm, description)
                print(f"🆕 Created landmark via /meta: {new_landmark.name}")
            else:
                print(f"📍 Using existing landmark: {new_landmark.name}")
        else:
            new_landmark = current_landmark

        # Paths
        old_path = os.path.join(crud.LANDMARKS_DIR, current_landmark.name, img.filename)
        new_folder = crud.ensure_landmark_folder(new_landmark.name)
        new_path = os.path.join(new_folder, img.filename)

        # Move file if path changed
        if old_path != new_path and os.path.exists(old_path):
            moved_path = move_image(old_path, new_folder)
            print(f"📦 Moved image: {old_path} -> {moved_path}")
            new_path = moved_path  # use real path returned
        else:
            print("↪ No move needed (path same or file missing)")

        # Update DB
        img.landmark_id = new_landmark.id

        if hasattr(img, "description") and description is not None:
            img.description = description

        try:
            if hasattr(img, "latitude") and latitude not in (None, "", "null"):
                img.latitude = float(latitude)
            if hasattr(img, "longitude") and longitude not in (None, "", "null"):
                img.longitude = float(longitude)
        except Exception:
            pass

        db.commit()
        db.refresh(img)

        # Re-embed FAISS for this image + place
        try:
            embedder = get_embedder()
            search = get_search_engine()

            pil_img = Image.open(new_path).convert("RGB")
            emb = embedder.generate_embedding(pil_img)

            search.add_landmark(
                embedding=emb,
                place_name=new_landmark.name,
                image_path=new_path,
            )

            print(f"🧠 FAISS updated for '{new_landmark.name}' via /meta")

        except Exception as e:
            print(f"⚠ Failed FAISS meta update: {e}")

        return {
            "status": "updated",
            "landmark": new_landmark.name,
            "image_id": img.id,
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------
# Move Image (legacy helper)
# ---------------------------------------------------
@app.post("/feedback/move")
async def move_feedback_image(
    image_path: str = Form(...),
    new_landmark: str = Form(...),
):
    try:
        if not os.path.exists(image_path):
            raise HTTPException(400, "Invalid image path")

        normalized = normalize_name(new_landmark)
        new_folder = os.path.join(crud.LANDMARKS_DIR, normalized)

        moved_path = move_image(image_path, new_folder)
        return {"message": "Image moved", "new_path": moved_path}

    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------
# Place Info (Wikipedia)
# ---------------------------------------------------
@app.get("/placeinfo/{name}", response_model=PlaceInfoResponse)
async def get_place_info(name: str, use_ai_summary: bool = False):
    try:
        import requests

        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            data = r.json()
            desc = data.get("extract", "")
            link = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            summary = desc.split("\n")[0] if use_ai_summary else None

            return PlaceInfoResponse(
                name=name,
                description=desc,
                summary=summary,
                wikipedia_url=link,
            )

        return PlaceInfoResponse(
            name=name,
            description="Information not found.",
            summary=None,
            wikipedia_url=None,
        )
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------
# Chat — HTML Output
# ---------------------------------------------------
@app.post("/chat/place")
async def chat_place(
    name: str = Form(...),
    user_message: Optional[str] = Form(None),
):
    try:
        system_prompt = f"""
You are a friendly and knowledgeable travel guide.
Respond ONLY in valid HTML (no markdown, no JSON).
Rules:
- Use <p>, <strong>, <em>, <ul>, <li>.
- No <html>, <body>, <head>.
- Max 120 words.
Topic: {name}
"""
        if user_message:
            system_prompt += f"\nUser asked: {user_message}"

        ai_resp = call_gemini(system_prompt)
        return {"place": name, "ai_response": ai_resp}

    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------
# Run (local dev)
# ---------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
