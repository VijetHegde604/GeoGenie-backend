#!/bin/bash
# Setup script for GeoGenie backend

echo "Setting up GeoGenie backend..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Build sample database
echo "Building sample database..."
python build_db.py

echo "Setup complete!"
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload"

