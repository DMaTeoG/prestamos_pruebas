#!/usr/bin/env bash
set -euo pipefail

APP_VERSION="${APP_VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo 'local')}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/api/v1/health/}"
IMAGE_NAME="prestamos-backend"
HAS_PREVIOUS=false

echo "=== [CD] Starting simulated deployment for version: ${APP_VERSION} ==="

# 1. Backup current image as :previous for rollback
if docker image inspect "${IMAGE_NAME}:latest" >/dev/null 2>&1; then
  echo "[CD] Tagging current ${IMAGE_NAME}:latest -> ${IMAGE_NAME}:previous"
  docker tag "${IMAGE_NAME}:latest" "${IMAGE_NAME}:previous"
  HAS_PREVIOUS=true
else
  echo "[CD] No existing :latest image found (first deployment)."
fi

# 2. Build new image
echo "[CD] Building ${IMAGE_NAME}:${APP_VERSION}..."
docker build -f docker/backend.Dockerfile -t "${IMAGE_NAME}:${APP_VERSION}" -t "${IMAGE_NAME}:latest" .

# 3. Deploy new container
echo "[CD] Deploying container with APP_VERSION=${APP_VERSION}..."
APP_VERSION="${APP_VERSION}" docker compose up -d db backend

# 4. Healthcheck verification
check_health() {
  local retries=15
  local wait_secs=2
  for i in $(seq 1 "${retries}"); do
    if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
      echo "[CD] Healthcheck passed on attempt ${i}/${retries}."
      return 0
    fi
    echo "[CD] Waiting for backend health (${i}/${retries})..."
    sleep "${wait_secs}"
  done
  return 1
}

if check_health; then
  echo "=== [CD] Deployment SUCCEEDED (${APP_VERSION}) ==="
  python scripts/notify_telegram.py \
    --title "CD Despliegue Exitoso" \
    --status "SUCCESS" \
    --version "${APP_VERSION}" \
    --details "Healthcheck OK en ${HEALTH_URL}"
  exit 0
fi

# 5. Automatic Rollback
echo "=== [CD] Healthcheck FAILED! Initiating automatic rollback ==="
if [ "${HAS_PREVIOUS}" = true ]; then
  docker tag "${IMAGE_NAME}:previous" "${IMAGE_NAME}:latest"
  APP_VERSION="previous" docker compose up -d backend
  if check_health; then
    echo "=== [CD] Rollback to :previous SUCCEEDED ==="
    python scripts/notify_telegram.py \
      --title "CD Rollback Automático" \
      --status "ROLLBACK" \
      --version "${APP_VERSION}" \
      --details "Falló healthcheck; revertido a imagen :previous"
    exit 1
  fi
fi

echo "=== [CD] Rollback FAILED or no :previous image available ==="
python scripts/notify_telegram.py \
  --title "CD Fallo Crítico" \
  --status "FAILED" \
  --version "${APP_VERSION}" \
  --details "Falló healthcheck y no fue posible hacer rollback"
exit 1
