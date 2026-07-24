#!/usr/bin/env bash
# Preflight guard for tasks/common/checkout-multi-service-outage: asserts the
# fixture is present AND still structurally broken (faults A and B, the two
# cheaply checkable via a single field read) before the agent runs. Exits
# nonzero, loudly, otherwise.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/isorun/_guards.sh
source "$SCRIPT_DIR/../_guards.sh"

GRADED_NS="checkout"
NS="${NAMESPACE:-$GRADED_NS}"

fail() {
  echo "PREFLIGHT FAIL [checkout-multi-service-outage]: $*" >&2
  exit 1
}

# tasks/common/checkout-multi-service-outage/task.yaml's verification_entries
# hardcode namespace: checkout in every check; grading always targets that
# namespace regardless of what NAMESPACE this preflight is invoked with.
if [[ "$NS" != "$GRADED_NS" ]]; then
  fail "namespace mismatch. Requested namespace '$NS' (\$NAMESPACE) does not match the namespace tasks/common/checkout-multi-service-outage/task.yaml actually grades ('$GRADED_NS'). Unset NAMESPACE or set it to '$GRADED_NS'."
fi

if ! iso_resource_exists deployment storefront-edge "$NS"; then
  fail "fixture ABSENT. deployment/storefront-edge does not exist in namespace $NS. Run scripts/isorun/seed/checkout-multi-service-outage.sh first, or run.sh without --no-seed."
fi

# Fault A: storefront-edge readinessProbe port must still be the broken 9999.
probe_port="$(kubectl get deployment storefront-edge -n "$NS" \
  -o jsonpath='{.spec.template.spec.containers[0].readinessProbe.httpGet.port}')"
case "$probe_port" in
  9999)
    : ;;
  8080)
    fail "ALREADY FIXED, re-seed. storefront-edge readinessProbe port is already 8080 before the agent ran. Re-seed with scripts/isorun/seed/checkout-multi-service-outage.sh." ;;
  *)
    fail "fixture MALFORMED. storefront-edge readinessProbe port='${probe_port}', expected the broken value '9999'." ;;
esac

# Fault B: inventory-db Service selector must still be the mismatched value.
if ! iso_resource_exists service inventory-db "$NS"; then
  fail "fixture ABSENT. service/inventory-db does not exist in namespace $NS. Run scripts/isorun/seed/checkout-multi-service-outage.sh first, or run.sh without --no-seed."
fi
db_selector="$(kubectl get service inventory-db -n "$NS" \
  -o jsonpath='{.spec.selector.app}')"
case "$db_selector" in
  inventory-db-renamed)
    : ;;
  inventory-db)
    fail "ALREADY FIXED, re-seed. service/inventory-db selector is already 'app=inventory-db' before the agent ran. Re-seed with scripts/isorun/seed/checkout-multi-service-outage.sh." ;;
  *)
    fail "fixture MALFORMED. service/inventory-db selector app='${db_selector}', expected the broken value 'inventory-db-renamed'." ;;
esac

echo "PREFLIGHT OK [checkout-multi-service-outage]: storefront-edge and inventory-db present with faults A and B intact (readinessProbe port 9999, mismatched Service selector)."
