#!/bin/bash
# Multiplatform Docker build script for GeoGenie backend
# Builds a single multiplatform image: latest (AMD64 + ARM64)
# Docker automatically selects the correct architecture when pulling/running

set -e

IMAGE_NAME="${1:-vijethegde/geogenie}"

echo "🐳 Building multiplatform Docker image: ${IMAGE_NAME}:latest"
echo "📦 Platforms: linux/amd64, linux/arm64"
echo "   (Docker will automatically select the correct architecture)"

# Create a new buildx builder instance if it doesn't exist
if ! docker buildx ls | grep -q multiplatform-builder; then
    echo "📦 Creating new buildx builder instance..."
    docker buildx create --name multiplatform-builder --use --bootstrap
else
    echo "✅ Using existing buildx builder instance..."
    docker buildx use multiplatform-builder
fi

# Build and push multiplatform image with 'latest' tag
# This single tag contains BOTH architectures
echo ""
echo "🔨 Building multiplatform image (latest) for AMD64 and ARM64..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag ${IMAGE_NAME}:latest \
    --push \
    --file Dockerfile \
    .

echo ""
echo "✅ Multiplatform build complete!"
echo "📦 ${IMAGE_NAME}:latest (contains both AMD64 and ARM64)"
echo ""
echo "✨ You can use the same tag everywhere - Docker selects the right architecture!"
echo ""
echo "To build locally for your current platform only (faster):"
echo "  docker build -t ${IMAGE_NAME}:local ."
echo ""
echo "To build and load for a specific platform:"
echo "  docker buildx build --platform linux/amd64 --load -t ${IMAGE_NAME}:amd64 ."
echo "  docker buildx build --platform linux/arm64 --load -t ${IMAGE_NAME}:arm64 ."
