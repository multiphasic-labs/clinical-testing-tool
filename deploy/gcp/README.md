# Google Cloud deployment (internal-first)

This deploys:

- **API service** on **Cloud Run** (FastAPI)
- **Worker service** on **Cloud Run** (RQ worker consuming Redis queue)
- **Database** on **Cloud SQL for Postgres**
- **Queue** on **Memorystore for Redis**

The app uses these env vars:

- `SAFETY_PLATFORM_DB_URL` (Postgres SQLAlchemy URL)
- `SAFETY_PLATFORM_REDIS_URL` (Redis URL)
- `SAFETY_PLATFORM_API_KEY` (optional; enables `x-api-key` auth on `/runs*`)
- `SAFETY_PLATFORM_ARTIFACTS` (optional; defaults inside container)

## 1) Prereqs

- `gcloud` installed and authenticated
- A GCP project selected:

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
```

Enable APIs:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com sqladmin.googleapis.com redis.googleapis.com vpcaccess.googleapis.com secretmanager.googleapis.com
```

## 2) Create Cloud SQL (Postgres)

Create instance:

```bash
gcloud sql instances create safety-platform-pg \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

Create DB + user:

```bash
gcloud sql databases create safety_platform --instance=safety-platform-pg
gcloud sql users create safety --instance=safety-platform-pg --password='CHANGE_ME'
```

Cloud Run connects via the **Cloud SQL unix socket** mounted at `/cloudsql/INSTANCE_CONNECTION_NAME`.

Get instance connection name:

```bash
gcloud sql instances describe safety-platform-pg --format='value(connectionName)'
```

Set `SAFETY_PLATFORM_DB_URL` like:

```text
postgresql+psycopg2://safety:CHANGE_ME@/safety_platform?host=/cloudsql/INSTANCE_CONNECTION_NAME
```

## 3) Create Memorystore (Redis)

Memorystore needs a VPC and Cloud Run needs a **Serverless VPC Access connector**.

Create a connector:

```bash
gcloud compute networks vpc-access connectors create safety-platform-conn \
  --network=default \
  --region=us-central1 \
  --range=10.8.0.0/28
```

Create Redis:

```bash
gcloud redis instances create safety-platform-redis \
  --region=us-central1 \
  --tier=basic \
  --size=1 \
  --redis-version=redis_7_0
```

Get Redis host:

```bash
gcloud redis instances describe safety-platform-redis --region=us-central1 --format='value(host)'
```

Set `SAFETY_PLATFORM_REDIS_URL` like:

```text
redis://REDIS_HOST:6379/0
```

## 4) Build and deploy to Cloud Run

### Option A: one-command deploy script (recommended)

1) Copy the template:

```bash
cp deploy/gcp/env.example deploy/gcp/env.local
```

2) Edit `deploy/gcp/env.local` with your project/instance/redis values.

3) Deploy:

```bash
chmod +x deploy/gcp/deploy.sh
./deploy/gcp/deploy.sh
```

### Option B: manual commands

From repo root (`mental-health-tester/`):

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/safety-platform:latest .
```

### Deploy API service

```bash
export INSTANCE_CONNECTION_NAME="$(gcloud sql instances describe safety-platform-pg --format='value(connectionName)')"
export DB_URL="postgresql+psycopg2://safety:CHANGE_ME@/safety_platform?host=/cloudsql/${INSTANCE_CONNECTION_NAME}"
export REDIS_URL="redis://REDIS_HOST:6379/0"

gcloud run deploy safety-platform-api \
  --image gcr.io/YOUR_PROJECT_ID/safety-platform:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --set-env-vars "SAFETY_PLATFORM_DB_URL=${DB_URL},SAFETY_PLATFORM_REDIS_URL=${REDIS_URL},SAFETY_PLATFORM_API_KEY=" \
  --port 8080 \
  --vpc-connector safety-platform-conn \
  --vpc-egress private-ranges-only
```

### Deploy Worker service

Same image, different command:

```bash
gcloud run deploy safety-platform-worker \
  --image gcr.io/YOUR_PROJECT_ID/safety-platform:latest \
  --region us-central1 \
  --no-allow-unauthenticated \
  --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --set-env-vars "SAFETY_PLATFORM_DB_URL=${DB_URL},SAFETY_PLATFORM_REDIS_URL=${REDIS_URL}" \
  --command python \
  --args -m,platform_api.rq_worker \
  --vpc-connector safety-platform-conn \
  --vpc-egress private-ranges-only
```

Now open:

- API docs: `https://.../docs`
- UI: `https://.../ui`

## Notes

- Cloud Run can scale worker instances; Redis queue ensures jobs are not lost if the API restarts.
- Artifacts currently write to the container filesystem. For a real production setup, we should move artifacts to **Google Cloud Storage** and store GCS URIs in `runs.artifacts_dir` (or a new field).

