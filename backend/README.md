# GeoGenie Backend

FastAPI server for landmark recognition using CLIP embeddings and GPS metadata.

## Setup

1. Install Python 3.10+
2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Build sample database:
```bash
python build_db.py
```

## Running

Start the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or use Python directly:
```bash
python main.py
```

Server will be available at `http://localhost:8000`

API docs available at `http://localhost:8000/docs`

