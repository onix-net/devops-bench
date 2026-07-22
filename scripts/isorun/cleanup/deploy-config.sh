#!/usr/bin/env bash
# Pre-run reset for tasks/gcp/deploy-config. Idempotent: safe to run when
# nothing exists.
set -euo pipefail

: "${CLUSTER:=autopilot-cluster-1}"
: "${PROJECT:=}"
: "${REGION:=us-central1}"
: "${NAMESPACE:=default}"

echo "==> deploy-config cleanup: deleting hypercomputer-d1-vllm-server deploy/svc/hpa in namespace 'default' (cluster: $CLUSTER)"
kubectl -n default delete deploy/hypercomputer-d1-vllm-server svc/hypercomputer-d1-vllm-service hpa/hypercomputer-d1-vllm-hpa --ignore-not-found
