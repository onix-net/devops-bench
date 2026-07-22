#!/usr/bin/env bash
# Pre-run reset for tasks/gcp/fix-config. Idempotent: safe to run when the
# deployment doesn't exist.
set -euo pipefail

: "${CLUSTER:=autopilot-cluster-1}"
: "${PROJECT:=}"
: "${REGION:=us-central1}"
: "${NAMESPACE:=default}"

# The tofu seed re-creates this deployment (broken) under --infra; under
# --no-infra reuse of an ambient cluster, deleting it resets the fixture.
echo "==> fix-config cleanup: deleting deploy/hypercomputer-d1-frontend in namespace 'default' (cluster: $CLUSTER)"
kubectl -n default delete deploy/hypercomputer-d1-frontend --ignore-not-found
