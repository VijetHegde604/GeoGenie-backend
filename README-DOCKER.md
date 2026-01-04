# Docker Multiplatform Build Guide

This guide explains how to build Docker images for multiple platforms (AMD64/x86_64 and ARM64/Raspberry Pi 5).

## Prerequisites

1. **Docker Buildx** (included with Docker Desktop, or install separately)
   ```bash
   # Check if buildx is available
   docker buildx version
   ```

2. **Docker Hub account** (for pushing images) or registry access

## Quick Start

### Build and Push Multiplatform Image (Single Tag)

```bash
./build-docker.sh [IMAGE_NAME]
```

Example:
```bash
./build-docker.sh vijethegde/geogenie
```

This will build and push a **single multiplatform image**:
- `vijethegde/geogenie:latest` contains **both** AMD64 and ARM64 architectures
- Docker automatically selects the correct architecture when you pull/run
- Use the same tag everywhere - no need to specify platform-specific tags!

### Build Locally for Current Platform (Faster)

If you only need to build for your current platform:

```bash
docker build -t vijethegde/geogenie:latest .
```

### Build for Specific Platform Only

For ARM64 (Raspberry Pi 5):
```bash
docker buildx build --platform linux/arm64 --load -t vijethegde/geogenie:pi .
```

For AMD64/x86_64:
```bash
docker buildx build --platform linux/amd64 --load -t vijethegde/geogenie:latest .
```

## How It Works

The Dockerfile automatically detects the target architecture using Docker Buildx's `TARGETARCH` build argument:

- **ARM64** → Uses `requirements-pi.txt` (optimized for Raspberry Pi 5)
- **AMD64/x86_64** → Uses `requirements.txt` (includes NVIDIA CUDA packages if needed)

## Architecture Detection

The Dockerfile uses this logic:
```dockerfile
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        REQ_FILE=requirements-pi.txt; \
    else \
        REQ_FILE=requirements.txt; \
    fi
```

## Using the Images

### docker-compose.yml

Use the same image tag everywhere - Docker automatically selects the correct architecture:

```yaml
services:
  geogenie:
    image: vijethegde/geogenie:latest  # Works on both AMD64 and ARM64!
    # ... rest of config
```

**No need to change the tag based on platform!** Docker will automatically pull the correct architecture-specific image.

### Manual Pull

```bash
# On x86_64 system
docker pull vijethegde/geogenie:latest  # Pulls AMD64 version

# On ARM64 system (Raspberry Pi 5)
docker pull vijethegde/geogenie:latest  # Pulls ARM64 version
```

Same command, different architectures automatically!

## Requirements Files

- **`requirements.txt`**: For x86_64 systems
  - Includes NVIDIA CUDA packages (for GPU support if available)
  - Pinned faiss-cpu version (1.7.4)

- **`requirements-pi.txt`**: For ARM64 (Raspberry Pi 5)
  - No NVIDIA packages
  - Unpinned faiss-cpu (allows compatible ARM builds)
  - PyTorch CPU-only builds

## Understanding the Build Process

When you build a multiplatform image, you'll see output like this:

```
[linux/amd64 2/9] RUN apt-get update...
[linux/arm64 2/9] RUN apt-get update...
```

This is **normal and expected**. Docker Buildx builds each platform separately in parallel because:
- Each architecture requires different binaries and dependencies
- The builds are completely independent
- Building in parallel is more efficient than sequential builds

Each platform gets its own build process, and the final image manifest contains both architectures. When someone pulls the image, Docker automatically selects the correct architecture for their platform.

## Complete Workflow with Docker Hub

### 1. Build and Push (from your local AMD64 machine)

```bash
./build-docker.sh vijethegde/geogenie
```

**What happens:**
- Builds AMD64 image (native, fast)
- Builds ARM64 image (via QEMU emulation, slower)
- **Pushes BOTH to Docker Hub under the same tag** (`vijethegde/geogenie:latest`)
- Docker Hub stores both architectures in a single manifest

### 2. Docker Hub Storage

When you push to Docker Hub:
- ✅ Both AMD64 and ARM64 images are stored
- ✅ They're linked together under the `:latest` tag
- ✅ Docker Hub creates a "manifest list" that points to both architectures
- ✅ Same tag, multiple architectures

### 3. Pull on Any Platform

**On your AMD64/x86_64 machine:**
```bash
docker pull vijethegde/geogenie:latest
# Docker Hub automatically serves the AMD64 version
```

**On your Raspberry Pi (ARM64):**
```bash
docker pull vijethegde/geogenie:latest
# Docker Hub automatically serves the ARM64 version (no NVIDIA packages!)
```

**Same command, different architectures automatically selected!** 🎉

### Building from Your Local Machine

✅ **You MUST build multiplatform images from your AMD64/x86_64 machine!**

**Important:** Building multiplatform images works best (and often only works) from AMD64 machines:
- ✅ AMD64 build runs natively on your machine (fast)
- ✅ ARM64 build runs via QEMU emulation (included with Docker Buildx)
- ✅ Each build uses the correct requirements file automatically:
  - ARM64 → `requirements-pi.txt` (no NVIDIA packages)
  - AMD64 → `requirements.txt` (includes NVIDIA packages)

❌ **Cannot build AMD64 images on ARM64 (Raspberry Pi):**
- Raspberry Pi can only build ARM64 natively
- Building AMD64 on ARM64 will fail
- That's why you need to build from your AMD64 machine!

**Workflow:**
1. Build on your AMD64/x86_64 machine → creates both architectures
2. Push to Docker Hub → stores both architectures
3. Pull on Raspberry Pi → gets ARM64 version automatically
4. Pull on AMD64 machine → gets AMD64 version automatically

**No need to build on the Raspberry Pi!** Build once from your local AMD64 machine and push. Then pull the image anywhere - Docker will automatically serve the correct architecture.

## Troubleshooting

### Buildx Builder Not Found

If you see errors about buildx builder:
```bash
docker buildx create --name multiplatform-builder --use --bootstrap
```

### Building Takes Too Long

Multiplatform builds are slower because they build for multiple architectures. For faster local development, build only for your current platform:
```bash
docker build -t geogenie:local .
```

### Testing ARM64 Image on x86_64

You can use QEMU emulation (slower but works):
```bash
docker run --platform linux/arm64 vijethegde/geogenie:latest
```

## Best Practices

1. **Tag your images**: Use semantic versioning (e.g., `v1.0.0`) in addition to `latest`
2. **Build on CI/CD**: Consider building multiplatform images in GitHub Actions or similar
3. **Test locally first**: Build for your platform first before doing multiplatform builds
4. **Use .dockerignore**: Exclude unnecessary files to speed up builds (already included)
