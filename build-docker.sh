#!/bin/bash
# GeoGenie Docker build script
# - AMD64 → :latest (and :amd64)
# - ARM64 → :pi (and :arm64)
# - Optional multiplatform :latest (AMD64 only, or both if desired)

set -e

# Default image name
IMAGE_NAME="${1:-vijethegde/geogenie}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🐳 GeoGenie Docker Build Script${NC}"
echo -e "Image: ${BLUE}${IMAGE_NAME}${NC}"
echo

# Architecture selection
echo "Which architecture(s) do you want to build?"
echo "1) AMD64 only → tags: latest, amd64"
echo "2) ARM64 only → tags: pi, arm64"
echo "3) Both → builds AMD64 (:latest) + ARM64 (:pi), optional multi-arch manifest"
echo
read -p "Enter choice (1/2/3) [default: 3]: " choice
choice=${choice:-3}

case $choice in
    1)
        PLATFORMS="linux/amd64"
        REQ_FILE="requirements.txt"
        TAGS="${IMAGE_NAME}:latest ${IMAGE_NAME}:amd64"
        echo -e "${GREEN}✅ Building AMD64 → :latest and :amd64${NC}"
        BUILD_AMD64=true
        ;;
    2)
        PLATFORMS="linux/arm64"
        REQ_FILE="requirements-pi.txt"
        TAGS="${IMAGE_NAME}:pi ${IMAGE_NAME}:arm64"
        echo -e "${GREEN}✅ Building ARM64 → :pi and :arm64${NC}"
        BUILD_ARM64=true
        ;;
    3)
        echo -e "${GREEN}✅ Building both architectures${NC}"
        echo "   • AMD64 → :latest and :amd64"
        echo "   • ARM64 → :pi and :arm64"
        BUILD_AMD64=true
        BUILD_ARM64=true
        ;;
    *)
        echo -e "${RED}Invalid choice. Aborting.${NC}"
        exit 1
        ;;
esac

# Push confirmation
echo
read -p "Do you want to PUSH the image(s) to the registry? (y/n) [n]: " push_confirm
push_confirm=${push_confirm:-n}

if [[ "$push_confirm" =~ ^[Yy]$ ]]; then
    PUSH_FLAG="--push"
    LOAD_FLAG=""
    echo -e "${GREEN}🚀 Images will be pushed.${NC}"
else
    PUSH_FLAG=""
    LOAD_FLAG="--load"  # Only works for single-platform builds
    echo -e "${YELLOW}📦 Images will be built and loaded locally (if single platform).${NC}"
fi

# Setup buildx builder
if ! docker buildx ls | grep -q multiplatform-builder; then
    echo
    echo "📦 Creating buildx builder instance..."
    docker buildx create --name multiplatform-builder --use --bootstrap
else
    docker buildx use multiplatform-builder
fi

# Function to build a platform
build_platform() {
    local platform=$1
    local req_file=$2
    local tags=$3

    echo
    echo -e "${GREEN}🔨 Building ${platform} with ${req_file}...${NC}"
    echo "   Tags: ${tags}"

    docker buildx build \
        --platform ${platform} \
        --build-arg REQ_FILE=${req_file} \
        $(for tag in ${tags}; do echo --tag $tag; done) \
        ${PUSH_FLAG} \
        ${LOAD_FLAG} \
        --file Dockerfile \
        .
}

# Execute builds
if [[ $BUILD_AMD64 ]]; then
    build_platform "linux/amd64" "requirements.txt" "${IMAGE_NAME}:latest ${IMAGE_NAME}:amd64"
fi

if [[ $BUILD_ARM64 ]]; then
    build_platform "linux/arm64" "requirements-pi.txt" "${IMAGE_NAME}:pi ${IMAGE_NAME}:arm64"
fi

# Optional: Create multi-arch :latest (AMD64 + ARM64)
if [[ $BUILD_AMD64 && $BUILD_ARM64 && "$push_confirm" =~ ^[Yy]$ ]]; then
    echo
    read -p "Create multi-arch :latest tag containing BOTH AMD64 and ARM64? (y/n) [n]: " multi_latest
    multi_latest=${multi_latest:-n}

    if [[ "$multi_latest" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}📦 Creating multi-arch manifest for :latest (AMD64 + ARM64)${NC}"
        docker manifest create ${IMAGE_NAME}:latest \
            --amend ${IMAGE_NAME}:amd64 \
            --amend ${IMAGE_NAME}:pi

        docker manifest push ${IMAGE_NAME}:latest

        echo -e "${GREEN}✅ Multi-arch :latest now includes both architectures!${NC}"
        echo "   • x86_64 machines → get AMD64 version"
        echo "   • ARM64 machines → get Pi-optimized version"
    else
        echo -e "${YELLOW}ℹ️  Multi-arch :latest not created. :latest remains AMD64-only.${NC}"
    fi
fi

echo
echo -e "${GREEN}🎉 Build complete!${NC}"
echo
echo "Available tags:"
[[ $BUILD_AMD64 ]] && echo "   • ${IMAGE_NAME}:latest   (AMD64)"
[[ $BUILD_AMD64 ]] && echo "   • ${IMAGE_NAME}:amd64   (AMD64)"
[[ $BUILD_ARM64 ]] && echo "   • ${IMAGE_NAME}:pi      (ARM64 / Raspberry Pi)"
[[ $BUILD_ARM64 ]] && echo "   • ${IMAGE_NAME}:arm64   (ARM64)"
echo
echo "Usage:"
echo "   Desktop/Server: docker pull ${IMAGE_NAME}:latest"
echo "   Raspberry Pi:   docker pull ${IMAGE_NAME}:pi"
