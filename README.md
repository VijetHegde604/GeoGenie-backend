# GeoGenie Backend

GeoGenie Backend is a FastAPI service for landmark recognition from photos, landmark catalog management, feedback ingestion, and place information/chat enrichment.

> This repository has been refreshed for current setup/documentation without changing API behavior or UX flow.

## What this service does

- Image recognition with a **GPS-first** strategy (EXIF or submitted coordinates).
- Visual fallback using **embedding similarity** + **FAISS**.
- Landmark CRUD-like operations for adding and listing landmarks.
- Feedback ingestion pipeline that stores uploaded images and updates search vectors.
- Place information retrieval via Wikipedia summary API.
- Place chat endpoint that returns compact HTML answers (for frontend rendering).

---

## Technology stack

- **API framework:** FastAPI + Uvicorn
- **ORM/database:** SQLAlchemy + SQLite (default local)
- **Vision/ML:** PyTorch, Transformers, FAISS, Pillow
- **Auth utilities:** JWT + HTTP Basic helper module (currently not wired to route dependencies)

---

## Repository layout

```text
GeoGenie-backend/
├── main.py                 # FastAPI app and HTTP routes
├── crud.py                 # DB and file operations
├── models.py               # SQLAlchemy models
├── db.py                   # DB engine/session/base
├── auth.py                 # Auth helpers (basic + JWT)
├── embed_generator.py      # Embedding model loader/generator
├── search_image.py         # FAISS index + search engine
├── exif_utils.py           # EXIF GPS extraction
├── geocode.py              # Reverse geocoder integration
├── ai_client.py            # Gemini chat client helper
├── build_db.py             # Build/refresh embedding DB
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-pi.txt
└── scripts/                # Utilities/evaluation scripts
```

---

## Quick start (local)

### 1) Prerequisites

- Python 3.10+ recommended
- pip + virtualenv

### 2) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Prepare data/index

```bash
python build_db.py
```

### 4) Run API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- API root: `http://localhost:8000/`
- OpenAPI docs: `http://localhost:8000/docs`

---

## API surface (current)

- `GET /` — health/status
- `GET /debug/routes` — route debug helper
- `POST /recognize` — landmark recognition from image + optional coordinates
- `GET /landmarks` — DB landmark list
- `GET /landmarks/list` — folder landmark list
- `POST /landmarks/add` — create landmark record/folder
- `POST /feedback/upload` — upload feedback image and optionally create landmark
- `POST /feedback/meta` — update image metadata/landmark association
- `POST /feedback/move` — move image between landmark folders
- `GET /placeinfo/{name}` — Wikipedia summary lookup
- `POST /chat/place` — place-focused HTML chat response

---

## Data and files

- Landmark images are stored under the landmarks directory managed by `crud.py`.
- Startup sync ensures folders and DB rows are aligned for discovered landmarks.
- Feedback uploads can append embeddings to FAISS for improved future matches.

---

## Notable maintenance updates applied

- Fixed coordinate handling edge case where `0.0` latitude/longitude could be ignored in request processing.
- Updated documentation to match the **actual current endpoints and behavior**.
- Clarified authentication status: helper module exists, but endpoints are currently open unless route dependencies are explicitly added.

---

## Development workflow

### Run server
```bash
uvicorn main:app --reload
```

### Rebuild embeddings/index
```bash
python build_db.py
```

### Optional utility scripts
See `scripts/` for dataset prep/evaluation helpers.

---

## Production notes

- Use a proper process manager (or container orchestrator) instead of reload mode.
- Set strict CORS origin list (avoid `*` in production).
- Configure `JWT_SECRET_KEY` if enabling route-level auth.
- Consider structured logging + monitoring before production rollout.

---

## Frontend

Frontend repository (as originally documented by project owner):

- <https://github.com/VijetHegde604/GeoGenie.git>

