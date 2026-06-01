#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Resolve variables (supporting standard GCP_PROJECT_ID and GKE_CLUSTER_NAME)
PROJECT_ID="${PROJECT_ID:-${GCP_PROJECT_ID:-}}"
CLUSTER_NAME="${CLUSTER_NAME:-${GKE_CLUSTER_NAME:-}}"

# Default values
NAMESPACE="${NAMESPACE:-production}"
LOCATION="${LOCATION:-${GCP_LOCATION:-us-central1-a}}"

# Verify required variables
if [ -z "${PROJECT_ID:-}" ] || [ -z "${CLUSTER_NAME:-}" ]; then
    echo "Error: PROJECT_ID (or GCP_PROJECT_ID) and CLUSTER_NAME (or GKE_CLUSTER_NAME) environment variables must be set."
    echo "Usage: PROJECT_ID=your-project CLUSTER_NAME=your-cluster LOCATION=zone ./setup.sh"
    exit 1
fi


echo "=== 1. Configuring gcloud and kubectl ==="
gcloud config set project "${PROJECT_ID}"
gcloud container clusters get-credentials "${CLUSTER_NAME}" --location "${LOCATION}"

echo "=== 2. Enabling GCP Secret Manager API ==="
gcloud services enable secretmanager.googleapis.com

echo "=== 3. Creating Secret in Cloud Secret Manager ==="
if gcloud secrets describe db-credentials >/dev/null 2>&1; then
    echo "Secret 'db-credentials' already exists."
else
    echo "Creating secret 'db-credentials'..."
    gcloud secrets create db-credentials --replication-policy="automatic"
fi

echo "Adding initial version (v1: compromised credential) to 'db-credentials'..."
echo -n "compromised-password-v1" | gcloud secrets versions add db-credentials --data-file=-

echo "=== 4. Checking and Installing External Secrets Operator (ESO) ==="
if kubectl get namespace external-secrets >/dev/null 2>&1; then
    echo "Namespace 'external-secrets' already exists."
else
    echo "Creating 'external-secrets' namespace..."
    kubectl create namespace external-secrets
fi

# Resolve Helm binary (download if not present globally)
if command -v helm &> /dev/null; then
    HELM_BIN="helm"
else
    echo "Local helm command not found. Downloading a standalone Helm binary..."
    curl -fsSL -o /tmp/helm.tar.gz https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz
    tar -C /tmp -zxf /tmp/helm.tar.gz linux-amd64/helm
    HELM_BIN="/tmp/linux-amd64/helm"
fi

if kubectl get crd clustersecretstores.external-secrets.io &>/dev/null; then
    echo "Custom Resource Definitions (CRDs) for External Secrets are already registered."
else
    echo "Applying Custom Resource Definitions (CRDs) for External Secrets..."
    kubectl apply -f "https://raw.githubusercontent.com/external-secrets/external-secrets/v0.9.11/deploy/crds/bundle.yaml" --server-side --force-conflicts
fi

if "${HELM_BIN}" list -n external-secrets | grep -q external-secrets; then
    echo "External Secrets Operator is already installed."
else
    echo "Installing External Secrets Operator via Helm..."
    "${HELM_BIN}" repo add external-secrets https://charts.external-secrets.io
    "${HELM_BIN}" repo update
    "${HELM_BIN}" install external-secrets external-secrets/external-secrets -n external-secrets --set installCRDs=true
    echo "Waiting for External Secrets Operator pods to be ready..."
    kubectl wait --namespace external-secrets \
      --for=condition=ready pod \
      --selector=app.kubernetes.io/instance=external-secrets \
      --timeout=90s
fi

echo "=== 5. Setting up Workload Identity & GCP Service Account ==="
GSA_NAME="secret-rotation-sa"
GSA_EMAIL="${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "${GSA_EMAIL}" >/dev/null 2>&1; then
    echo "GCP Service Account '${GSA_EMAIL}' already exists."
else
    echo "Creating GCP Service Account '${GSA_NAME}'..."
    gcloud iam service-accounts create "${GSA_NAME}" \
        --description="GSA for GKE ExternalSecrets Secret Manager access" \
        --display-name="secret-rotation-sa"
fi

echo "Granting Secret Manager Secret Accessor role to '${GSA_EMAIL}'..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${GSA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None

echo "Binding Kubernetes Service Account (external-secrets/external-secrets) to GCP Service Account..."
gcloud iam service-accounts add-iam-policy-binding "${GSA_EMAIL}" \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[external-secrets/external-secrets]" \
    --condition=None

echo "Annotating Kubernetes Service Account (external-secrets/external-secrets)..."
kubectl annotate serviceaccount external-secrets \
    --namespace external-secrets \
    --overwrite \
    iam.gke.io/gcp-service-account="${GSA_EMAIL}"

echo "=== 6. Applying Kubernetes manifests ==="
# Ensure target namespace exists
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Interpolate and apply manifests
sed "s/{{GCP_PROJECT_ID}}/${PROJECT_ID}/g" "${SCRIPT_DIR}/secret-store.yaml" | kubectl apply -f -
sed "s/{{NAMESPACE}}/${NAMESPACE}/g" "${SCRIPT_DIR}/external-secret.yaml" | kubectl apply -f -
sed "s/{{NAMESPACE}}/${NAMESPACE}/g" "${SCRIPT_DIR}/deployment.yaml" | kubectl apply -f -

echo "=== Setup Completed Successfully! ==="
echo "Verify external-secret sync status:"
echo "kubectl get externalsecret db-credentials -n ${NAMESPACE}"
echo "kubectl get secret db-credentials -n ${NAMESPACE} -o yaml"
