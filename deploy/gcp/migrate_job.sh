#!/usr/bin/env bash
# One-shot Alembic migrate via Cloud Run Job (same DB socket URL as deploy.sh).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "${HERE}/env.local" ]]; then
  # shellcheck disable=SC1091
  source "${HERE}/env.local"
else
  echo "Missing ${HERE}/env.local"
  exit 1
fi

: "${PROJECT_ID:?}"
: "${REGION:?}"
: "${IMAGE:?}"
: "${PG_INSTANCE:?}"
: "${PG_DB:?}"
: "${PG_USER:?}"
: "${PG_PASSWORD:?}"

JOB_NAME="${MIGRATE_JOB_NAME:-safety-platform-migrate}"
MEMORY="${MIGRATE_JOB_MEMORY:-1Gi}"

gcloud config set project "${PROJECT_ID}" >/dev/null

INSTANCE_CONNECTION_NAME="$(gcloud sql instances describe "${PG_INSTANCE}" --format='value(connectionName)')"
DB_URL="$(
  PG_USER="${PG_USER}" PG_PASSWORD="${PG_PASSWORD}" PG_DB="${PG_DB}" INSTANCE_CONNECTION_NAME="${INSTANCE_CONNECTION_NAME}" \
  python3 -c "
import os, urllib.parse
u = urllib.parse.quote(os.environ['PG_USER'], safe='')
p = urllib.parse.quote(os.environ['PG_PASSWORD'], safe='')
db = os.environ['PG_DB']
icn = os.environ['INSTANCE_CONNECTION_NAME']
print(f'postgresql+psycopg2://{u}:{p}@/{db}?host=/cloudsql/{icn}')
"
)"

echo "Deploying & running migration job ${JOB_NAME} (image=${IMAGE})"
gcloud run jobs deploy "${JOB_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --set-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --set-env-vars "SAFETY_PLATFORM_DB_URL=${DB_URL}" \
  --command=python \
  --args=-m,alembic,upgrade,head \
  --memory "${MEMORY}" \
  --max-retries 1 \
  --task-timeout 900 \
  --execute-now \
  --wait

echo "Migration job finished."
