#!/usr/bin/env bash
set -euo pipefail

TF_DIR="infra"
TF_VARS="${TF_DIR}/terraform.tfvars"
TF="terraform -chdir=${TF_DIR}"
IMG_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

check_tfvars() {
  if [ ! -f "$TF_VARS" ]; then
    echo "ERROR: ${TF_VARS} not found. Copy terraform.tfvars.example and fill in values."
    exit 1
  fi
}

# Read GEMINI_API_KEY from .env and pass it to Terraform via env var.
# TF_VAR_gemini_api_key overrides anything in terraform.tfvars.
load_env_secrets() {
  if [ -f .env ]; then
    local key
    key=$(grep GEMINI_API_KEY .env | cut -d'"' -f2 || true)
    if [ -n "$key" ]; then
      export TF_VAR_gemini_api_key="$key"
      echo "==> Loaded GEMINI_API_KEY from .env"
    fi
  fi

  if [ -z "${TF_VAR_gemini_api_key:-}" ]; then
    echo "ERROR: GEMINI_API_KEY not found. Set it in .env or export TF_VAR_gemini_api_key."
    exit 1
  fi
}

tf_out() {
  $TF output -raw "$1"
}

build_and_push_frontend() {
  local backend_url="$1"
  local registry="$2"
  local img="${registry}/frontend:${IMG_TAG}"

  echo "==> Building frontend image (VITE_API_URL=${backend_url})..."
  docker build --platform linux/amd64 --no-cache \
    --build-arg VITE_API_URL="$backend_url" \
    -t "$img" -f frontend/Dockerfile frontend/

  echo "==> Pushing frontend image..."
  docker push "$img"
}

# ── 1. Prepare ───────────────────────────────────────────────────────
#    Bootstraps infra (APIs, registry, secrets), builds & pushes the
#    backend image. Frontend is built in deploy (needs backend URL).
cmd_prepare() {
  check_tfvars
  load_env_secrets

  echo "==> Initializing Terraform..."
  $TF init

  echo "==> Bootstrapping APIs, registry, and secrets..."
  $TF apply -auto-approve \
    -target=google_project_service.apis \
    -target=google_artifact_registry_repository.diveroast \
    -target=google_service_account.backend \
    -target=google_secret_manager_secret.gemini_api_key \
    -target=google_secret_manager_secret_version.gemini_api_key \
    -target=google_secret_manager_secret_iam_member.backend_secret_access

  REGISTRY=$(tf_out artifact_registry)
  DOCKER_HOST=$(echo "$REGISTRY" | cut -d/ -f1)

  echo "==> Authenticating Docker with Artifact Registry..."
  gcloud auth configure-docker "$DOCKER_HOST" --quiet

  # ── Backend image ──
  BACKEND_IMG="${REGISTRY}/backend:${IMG_TAG}"
  echo "==> Building backend image (linux/amd64)..."
  docker build --platform linux/amd64 -t "$BACKEND_IMG" .

  echo "==> Pushing backend image..."
  docker push "$BACKEND_IMG"

  # ── Frontend image (placeholder — deploy rebuilds with real URL) ──
  build_and_push_frontend "" "$REGISTRY"

  echo ""
  echo "=============================="
  echo " Prepare complete!"
  echo "=============================="
  echo "  Backend:  ${BACKEND_IMG}"
  echo "  Frontend: ${REGISTRY}/frontend:${IMG_TAG}"
  echo ""
  echo "Run 'make deploy' to deploy all services."
}

# ── 2. Deploy ────────────────────────────────────────────────────────
#    Applies full Terraform config, then rebuilds the frontend with
#    the real backend URL and forces a new Cloud Run revision.
cmd_deploy() {
  check_tfvars
  load_env_secrets

  echo "==> Applying full Terraform configuration..."
  $TF apply -auto-approve \
    -var="backend_image_tag=${IMG_TAG}" \
    -var="frontend_image_tag=${IMG_TAG}"

  BACKEND_URL=$(tf_out backend_url)
  PHOENIX_URL=$(tf_out phoenix_url)
  FRONTEND_URL=$(tf_out frontend_url)
  REGISTRY=$(tf_out artifact_registry)
  DOCKER_HOST=$(echo "$REGISTRY" | cut -d/ -f1)

  # Rebuild frontend with the real backend URL
  gcloud auth configure-docker "$DOCKER_HOST" --quiet
  build_and_push_frontend "$BACKEND_URL" "$REGISTRY"

  # Force Cloud Run to pull the new image
  echo "==> Updating frontend Cloud Run service..."
  gcloud run services update diveroast-frontend \
    --region="$(tf_out region)" \
    --project="$(tf_out project_id)" \
    --image="${REGISTRY}/frontend:${IMG_TAG}" \
    --quiet

  echo ""
  echo "=============================="
  echo " Deployment complete!"
  echo "=============================="
  echo " Backend:  ${BACKEND_URL}"
  echo " Phoenix:  ${PHOENIX_URL}"
  echo " Frontend: ${FRONTEND_URL}"
  echo ""
  echo " Health check: curl ${BACKEND_URL}/health"
  echo "=============================="
}

# ── 3. Destroy ───────────────────────────────────────────────────────
#    Tears down all GCP resources. Empty buckets first (Terraform can't
#    delete non-empty buckets without force_destroy), then verify nothing
#    billable remains.
cmd_destroy() {
  check_tfvars
  load_env_secrets

  echo "==> Emptying GCS buckets before destroy..."
  PHOENIX_BUCKET=$(tf_out phoenix_traces_bucket 2>/dev/null || true)

  if [ -n "$PHOENIX_BUCKET" ]; then
    gsutil -m rm -r "gs://${PHOENIX_BUCKET}/*" 2>/dev/null || true
  fi

  echo "==> Destroying all Terraform resources..."
  $TF destroy -auto-approve

  PROJECT_ID=$(grep project_id "$TF_VARS" | head -1 | sed 's/.*= *"\(.*\)"/\1/')
  REGION=$(grep region "$TF_VARS" | head -1 | sed 's/.*= *"\(.*\)"/\1/')

  echo ""
  echo "==> Verifying cleanup..."
  DIRTY=0

  SERVICES=$(gcloud run services list --project="$PROJECT_ID" --region="$REGION" --format="value(name)" 2>/dev/null || true)
  if [ -n "$SERVICES" ]; then
    echo "  WARNING: Cloud Run services still exist: $SERVICES"
    DIRTY=1
  else
    echo "  Cloud Run services: clean"
  fi

  REPOS=$(gcloud artifacts repositories list --project="$PROJECT_ID" --location="$REGION" --format="value(name)" 2>/dev/null || true)
  if [ -n "$REPOS" ]; then
    echo "  WARNING: Artifact Registry repos still exist: $REPOS"
    DIRTY=1
  else
    echo "  Artifact Registry: clean"
  fi

  BUCKETS=$(gsutil ls -p "$PROJECT_ID" 2>/dev/null || true)
  if [ -n "$BUCKETS" ]; then
    echo "  WARNING: GCS buckets still exist: $BUCKETS"
    DIRTY=1
  else
    echo "  GCS buckets: clean"
  fi

  SECRETS=$(gcloud secrets list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null || true)
  if [ -n "$SECRETS" ]; then
    echo "  WARNING: Secrets still exist: $SECRETS"
    DIRTY=1
  else
    echo "  Secret Manager: clean"
  fi

  echo ""
  if [ "$DIRTY" -eq 0 ]; then
    echo "All GCP resources destroyed. Nothing billable remains."
  else
    echo "WARNING: Some resources may still exist. Check the warnings above."
  fi
}

# ── Dispatch ─────────────────────────────────────────────────────────
case "${1:-}" in
  prepare) cmd_prepare ;;
  deploy)  cmd_deploy ;;
  destroy) cmd_destroy ;;
  *)
    echo "Usage: $0 {prepare|deploy|destroy}"
    echo ""
    echo "Commands:"
    echo "  prepare  Bootstrap infra, build & push Docker images"
    echo "  deploy   Apply Terraform, rebuild frontend with backend URL, deploy"
    echo "  destroy  Tear down all GCP resources"
    echo ""
    echo "Secrets: GEMINI_API_KEY is read from .env (or export TF_VAR_gemini_api_key)"
    exit 1
    ;;
esac
