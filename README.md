# GeoGenie 🗺️

AI-powered React Native + Python app that identifies landmarks and monuments from photos using CLIP/DINOv2 embeddings and GPS EXIF metadata.

## Features

- 📸 **Photo Recognition**: Take or select photos to identify landmarks
- 🗺️ **GPS Integration**: Uses EXIF GPS data or live location for accurate identification
- 🤖 **AI-Powered**: CLIP embeddings for visual similarity matching
- 🌐 **Offline Support**: Basic matching works offline (with pre-built database)
- 📚 **Wikipedia Integration**: Fetches detailed information about recognized places
- 💬 **Feedback System**: Help improve recognition by providing corrections

## Project Structure

```
GeoGenie-backend/
    |                       # FastAPI Python server
    ├── main.py             # FastAPI app with endpoints
    ├── embed_generator.py  # CLIP embedding extraction
    ├── build_db.py         # Build reference embeddings database
    ├── search_image.py     # FAISS similarity search
    ├── exif_utils.py       # GPS metadata extraction
    ├── geocode.py          # Reverse geocoding
    └── requirements.txt

```

## Quick Start

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Build sample database:**
```bash
python build_db.py
```

5. **Start the server:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`


## API Endpoints

### POST /recognize
Recognize landmark from uploaded image.

**Request:**
- `image`: Multipart file upload
- `latitude` (optional): GPS latitude
- `longitude` (optional): GPS longitude

**Response:**
```json
{
  "place_name": "Eiffel Tower",
  "confidence": 0.92,
  "source": "visual",
  "coordinates": [48.8584, 2.2945]
}
```

### POST /feedback
Submit feedback for incorrect recognition.

**Request:**
```json
{
  "image_id": "optional_id",
  "place_name": "Correct Place Name",
  "coordinates": [48.8584, 2.2945]
}
```

### GET /placeinfo/{name}
Get place information from Wikipedia.

**Response:**
```json
{
  "name": "Eiffel Tower",
  "description": "Full Wikipedia description...",
  "summary": "AI-generated summary (if requested)",
  "wikipedia_url": "https://..."
}
```

## How It Works

1. **GPS-First Approach**: If GPS coordinates are available (from EXIF or live location), the app uses reverse geocoding via OpenStreetMap Nominatim API.

2. **Visual Fallback**: If GPS is unavailable or doesn't yield a landmark, the app:
   - Extracts CLIP/DinoV2 embeddings from the image
   - Searches against a FAISS database of reference landmarks
   - Returns the best match with confidence score

3. **Information Retrieval**: Once a landmark is identified, Wikipedia API provides detailed information.

## Building the Database

To add your own landmarks to the database:

1. Create a directory structure:
```
data/landmarks/
├── Eiffel Tower/
│   └── image1.jpg
├── Statue of Liberty/
│   └── image1.jpg
└── ...
```

2. Run:
```bash
python build_db.py
```

Or modify `build_db.py` to load from your own data source.

## Development Notes

### Backend
- Uses CLIP ViT-B/32 model from HuggingFace
- FAISS for efficient similarity search
- Pillow for image processing and EXIF extraction
- FastAPI with automatic OpenAPI documentation

### Future Enhancements
- On-device CLIP inference using ONNX Runtime Mobile
- Local SQLite database for top 500 landmarks (offline mode)
- GPT-4-mini integration for AI summaries
- Batch processing for multiple images
- User-contributed landmark database



