#!/usr/bin/env bash
# Seed hook for tasks/common/checkout-multi-service-outage: apply the
# broken-checkout-chain fixture, for fast local iteration against an
# already-standing cluster (no tofu, no cluster build).
#
# Fixture:
# tf/prebuilt/checkout-multi-service-outage-kind/manifests/checkout-multi-service-outage.yaml.
# Relies on scripts/isorun/cleanup/checkout-multi-service-outage.sh having
# already deleted the 'checkout' namespace this run (run.sh always runs
# cleanup before seed); this hook does no separate reset of its own.
set -euo pipefail

: "${CLUSTER:=devops-bench-kind}"
: "${PROJECT:=}"
: "${REGION:=local}"
: "${NAMESPACE:=checkout}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FIXTURE="$REPO_ROOT/tf/prebuilt/checkout-multi-service-outage-kind/manifests/checkout-multi-service-outage.yaml"

echo "==> checkout-multi-service-outage seed: SEED (apply $FIXTURE)"
kubectl apply -f "$FIXTURE"

echo "==> checkout-multi-service-outage seed: done. Four faults are present: storefront-edge readinessProbe port 9999, inventory-db Service selector mismatch, Ingress / only with Exact pathType, promo-banner literal env shadowing its ConfigMap."
