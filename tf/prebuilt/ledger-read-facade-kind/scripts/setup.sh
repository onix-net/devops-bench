#!/usr/bin/env bash
#
# Setup for the ledger-read-facade task. Runs from OUTSIDE the cluster during
# `tofu apply`, before the agent starts: waits for the ingress-nginx
# controller to be ready, then applies the broken ledger-read-facade fixture
# so the task provisions already-broken.
set -euo pipefail

export KUBECONFIG="${KUBECONFIG:?KUBECONFIG is required}"
MANIFESTS_DIR="${MANIFESTS_DIR:?MANIFESTS_DIR is required}"
MANIFESTS_DIR="$(cd "${MANIFESTS_DIR}" && pwd)"
NAMESPACE="${NAMESPACE:?NAMESPACE is required}"

# Belt-and-suspenders: tofu's helm_release already waits (wait=true) and the
# seed step depends_on the ingress module, so the controller should be ready.
# This explicit wait guards against a helm-reports-ready-before-pod-ready race;
# keep it.
echo "==> Waiting for the ingress-nginx controller to be ready..."
kubectl -n ingress-nginx wait --for=condition=ready pod -l app.kubernetes.io/component=controller --timeout=180s

echo "==> Applying the broken ${NAMESPACE} fixture (retrying to absorb any residual webhook race)..."
attempt=1
until kubectl apply -f "${MANIFESTS_DIR}/ledger-read-facade.yaml"; do
  if [[ "${attempt}" -ge 5 ]]; then
    echo "==> Failed to apply the fixture after ${attempt} attempts." >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 3
done

# No wait for workload readiness here: the fixture is intentionally broken
# (ledger-facade crash-loops), so a rollout/Available wait would hang
# provisioning on a deliberately-broken deployment.

echo "==> Setup complete. Namespace ${NAMESPACE} seeded with the broken ledger-read-facade fixture."
