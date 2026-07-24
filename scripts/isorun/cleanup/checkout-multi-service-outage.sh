#!/usr/bin/env bash
# Pre-run reset for tasks/common/checkout-multi-service-outage. Idempotent:
# safe to run when the namespace doesn't exist.
set -euo pipefail

: "${CLUSTER:=devops-bench-kind}"
: "${PROJECT:=}"
: "${REGION:=local}"
: "${NAMESPACE:=checkout}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/isorun/_guards.sh
source "$SCRIPT_DIR/../_guards.sh"
iso_refuse_protected_namespace "$NAMESPACE"

echo "==> checkout-multi-service-outage cleanup: deleting namespace '$NAMESPACE' (cluster: $CLUSTER)"
kubectl delete namespace "$NAMESPACE" --ignore-not-found --wait=true --timeout=120s
