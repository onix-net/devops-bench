#!/usr/bin/env bash
# Seed hook for tasks/common/ledger-read-facade: apply the broken-facade
# fixture, for fast local iteration against an already-standing cluster (no
# tofu, no cluster build).
#
# Fixture: scripts/isorun/fixtures/ledger-read-facade.yaml. Relies on
# scripts/isorun/cleanup/ledger-read-facade.sh having already deleted the
# 'ledger' namespace this run (run.sh always runs cleanup before seed); this
# hook does no separate reset of its own.
set -euo pipefail

: "${CLUSTER:=devops-bench-kind}"
: "${PROJECT:=}"
: "${REGION:=local}"
: "${NAMESPACE:=ledger}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURE="$SCRIPT_DIR/../fixtures/ledger-read-facade.yaml"

echo "==> ledger-read-facade seed: SEED (apply $FIXTURE)"
kubectl apply -f "$FIXTURE"

echo "==> ledger-read-facade seed: done. deploy/ledger-facade is present with no writable emptyDir mounts (broken); no NetworkPolicy or PodDisruptionBudget exist yet."
