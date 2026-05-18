# GeoGenie Docker Guide (Updated)

This document describes container builds and runtime for GeoGenie Backend on both AMD64 and ARM64.

## Files involved

- `Dockerfile`
- `docker-compose.yml`
- `build-docker.sh`
- `requirements.txt` (default)
- `requirements-pi.txt` (ARM-focused)

---

## Prerequisites

- Docker Engine with Buildx support
- Optional: Docker Hub account for pushing multiplatform images

Check Buildx:

```bash
docker buildx version
```

---

## Local build (single platform)

```bash
docker build -t geogenie-backend:local .
```

Run:

```bash
docker run --rm -p 8000:8000 geogenie-backend:local
```

---

## Multiplatform build + push

Using helper script:

```bash
./build-docker.sh <dockerhub-namespace/image>
```

Example:

```bash
./build-docker.sh vijethegde/geogenie
```

This publishes a multi-arch manifest for `:latest` (AMD64 + ARM64).

---

## Manual Buildx example

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t vijethegde/geogenie:latest \
  --push .
```

---

## Architecture-aware dependency selection

The Dockerfile uses `TARGETARCH` to choose requirements:

- `arm64` -> `requirements-pi.txt`
- otherwise -> `requirements.txt`

This keeps Raspberry Pi builds lighter and avoids incompatible GPU package assumptions.

---

## docker-compose

```bash
docker compose up --build
```

If using a published multi-arch image in `docker-compose.yml`, keep a single tag and let Docker resolve architecture automatically.

---

## Troubleshooting

### Missing builder
```bash
docker buildx create --name geogenie-builder --use --bootstrap
```

### Slow ARM build on AMD64
Expected: ARM layers may run under QEMU emulation.

### Validate exposed API
After container starts:

```bash
curl http://localhost:8000/
```

Expected JSON with service status.

---

## Recommended release practice

- Publish semantic tags (e.g., `v1.2.0`) in addition to `latest`.
- Build via CI for reproducibility.
- Smoke test `/` and `/docs` after every image publish.

