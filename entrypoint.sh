#!/bin/bash
set -e

FAISS_INDEX="/app/data/landmarks_db.faiss"
METADATA_PKL="/app/data/landmarks_metadata.pkl"

# Check if to force a rebuild OR if files are missing
if [ "$REBUILD_DB" = "true" ]; then
    echo "REBUILD_DB is set to true. Forcing a fresh database build..."
    python build_db.py /app/landmarks
elif [ ! -f "$FAISS_INDEX" ] || [ ! -f "$METADATA_PKL" ]; then
    echo "Database files not found. Initializing build from /app/landmarks..."
    python build_db.py /app/landmarks
else
    echo "Found existing FAISS index and metadata. Ready to start."
fi

# Hand off control to the FastAPI server
exec "$@"
