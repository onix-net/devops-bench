#!/usr/bin/env bash
# Pre-run reset for tasks/gcp/lustre-csi-deployment. Idempotent: safe to run
# when nothing exists.
set -euo pipefail

: "${CLUSTER:=autopilot-cluster-1}"
: "${PROJECT:=}"
: "${REGION:=us-central1}"
: "${NAMESPACE:=default}"

echo "==> lustre-csi-deployment cleanup: deleting gemma-inference-staging deploy/svc/pvc in namespace 'default' and the gemma-pv PV (cluster: $CLUSTER)"
kubectl -n default delete deploy/gemma-inference-staging svc/gemma-service pvc/gemma-pvc --ignore-not-found
kubectl delete pv/gemma-pv --ignore-not-found

# Do NOT touch the Lustre instance or its VPC here: tofu owns that lifecycle
# and tears it down (or reseeds it) on --infra runs.
