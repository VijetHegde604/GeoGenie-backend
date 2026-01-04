#!/bin/bash
# Multiplatform Docker build script for GeoGenie backend
# Builds images for both AMD64 and ARM64 architectures

set -e

IMAGE_NAME="${1:-vijethegde/geogenie}"
TAG="${2:-latest}"

echo "🐳 Building multiplatform Docker image: ${IMAGE_NAME}:${TAG}"
echo "📦 Platforms: linux/amd64, linux/arm64"

# Create a new buildx builder instance if it doesn't exist
if ! docker buildx ls | grep -q multiplatform-builder; then
    echo "📦 Creating new buildx builder instance..."
    docker buildx create --name multiplatform-builder --use --bootstrap
else
    echo "✅ Using existing buildx builder instance..."
    docker buildx use multiplatform-builder
fi

# Build and push for both platforms
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag ${IMAGE_NAME}:${TAG} \
    --push \
    --file Dockerfile \
    .

echo "✅ Multiplatform build complete!"
echo "📦 Image: ${IMAGE_NAME}:${TAG}"
echo "🏗️  Platforms: linux/amd64, linux/arm64"
echo ""
echo "To build locally for your current platform only (faster):"
echo "  docker build -t ${IMAGE_NAME}:${TAG} ."
echo ""
echo "To build and load for a specific platform:"
echo "  docker buildx build --platform linux/arm64 --load -t ${IMAGE_NAME}:pi ."
