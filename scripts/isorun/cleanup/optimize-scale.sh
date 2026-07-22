#!/usr/bin/env bash
# Pre-run reset for tasks/common/optimize-scale. Idempotent: safe to run when
# nothing exists.
set -euo pipefail

: "${CLUSTER:=autopilot-cluster-1}"
: "${PROJECT:=}"
: "${REGION:=us-central1}"

NS="${NAMESPACE:-default}"

# scale-target is the {{TARGET_DEPLOYMENT_NAME}} default; also sweep any HPA
# tagged with app=scale-target in case it was created under a different name.
echo "==> optimize-scale cleanup: deleting scale-target deploy/svc/hpa in namespace '$NS' (cluster: $CLUSTER)"
kubectl -n "$NS" delete deploy/scale-target svc/scale-target hpa/scale-target --ignore-not-found
kubectl -n "$NS" delete hpa -l app=scale-target --ignore-not-found
