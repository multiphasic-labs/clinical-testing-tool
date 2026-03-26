#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../.." && pwd)"

if [[ -f "${HERE}/env.local" ]]; then
  # shellcheck disable=SC1091
  source "${HERE}/env.local"
else
  echo "Missing ${HERE}/env.local"
  echo "Copy ${HERE}/env.example to env.local, edit, then run: source deploy/gcp/env.local"
  exit 1
fi

: "${PROJECT_ID:?}"
: "${REGION:?}"
: "${IMAGE:?}"
: "${PG_INSTANCE:?}"
: "${PG_DB:?}"
: "${PG_USER:?}"
: "${PG_PASSWORD:?}"
: "${REDIS_HOST:?}"
: "${VPC_CONNECTOR:?}"

echo "Using project=${PROJECT_ID} region=${REGION}"

gcloud config set project "${PROJECT_ID}" >/dev/null

INSTANCE_CONNECTION_NAME="$(gcloud sql instances describe "${PG_INSTANCE}" --format='value(connectionName)')"
DB_URL="postgresql+psycopg2://${PG_USER}:${PG_PASSWORD}@/${PG_DB}?host=/cloudsql/${INSTANCE_CONNECTION_NAME}"
REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT:-6379}/${REDIS_DB:-0}"

echo "Building image ${IMAGE}"
cd "${REPO_ROOT}"
gcloud builds submit --tag "${IMAGE}" .

echo "Deploying API service ${SERVICE_API:-safety-platform-api}"
gcloud run deploy "${SERVICE_API:-safety-platform-api}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --allow-unauthenticated \
  --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --set-env-vars "SAFETY_PLATFORM_DB_URL=${DB_URL},SAFETY_PLATFORM_REDIS_URL=${REDIS_URL},SAFETY_PLATFORM_QUEUE_NAME=${QUEUE_NAME:-default},SAFETY_PLATFORM_API_KEY=${SAFETY_PLATFORM_API_KEY:-}" \
  --port 8080 \
  --vpc-connector "${VPC_CONNECTOR}" \
  --vpc-egress private-ranges-only

echo "Deploying Worker service ${SERVICE_WORKER:-safety-platform-worker}"
gcloud run deploy "${SERVICE_WORKER:-safety-platform-worker}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --no-allow-unauthenticated \
  --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --set-env-vars "SAFETY_PLATFORM_DB_URL=${DB_URL},SAFETY_PLATFORM_REDIS_URL=${REDIS_URL},SAFETY_PLATFORM_QUEUE_NAME=${QUEUE_NAME:-default}" \
  --command python \
  --args -m,platform_api.rq_worker \
  --vpc-connector "${VPC_CONNECTOR}" \
  --vpc-egress private-ranges-only

API_URL="$(gcloud run services describe "${SERVICE_API:-safety-platform-api}" --region "${REGION}" --format='value(status.url)')"
echo ""
echo "Done."
echo "API: ${API_URL}"
echo "Docs: ${API_URL}/docs"
echo "UI:   ${API_URL}/ui"

