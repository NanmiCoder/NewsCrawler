#!/bin/bash
# Install dependencies for news_extractor_backend

set -e

echo "Installing dependencies for news_extractor_backend..."

# Try uv first
if command -v uv &> /dev/null; then
    echo "Using uv to install dependencies..."
    cd "$(dirname "$0")"
    uv pip install -r requirements.txt
else
    # Fallback to pip
    echo "uv not found, using pip..."
    python3 -m pip install -r requirements.txt
fi

echo "Dependencies installed successfully!"
echo ""
echo "To run tests:"
echo "  cd news_extractor_backend"
echo "  pytest"
echo ""
echo "To start the backend:"
echo "  cd news_extractor_backend"
echo "  uvicorn news_extractor_backend.main:app --reload"
