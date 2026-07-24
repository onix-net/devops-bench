#!/usr/bin/env bash
# Preflight guard for tasks/common/ledger-read-facade: asserts the fixture is
# present AND still structurally broken (no writable emptyDir mounts, no
# NetworkPolicy/PodDisruptionBudget yet) before the agent runs. Exits
# nonzero, loudly, otherwise.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/isorun/_guards.sh
source "$SCRIPT_DIR/../_guards.sh"

GRADED_NS="ledger"
NS="${NAMESPACE:-$GRADED_NS}"
DEPLOY="ledger-facade"

fail() {
  echo "PREFLIGHT FAIL [ledger-read-facade]: $*" >&2
  exit 1
}

# tasks/common/ledger-read-facade/task.yaml's verification_entries hardcode
# namespace: ledger in every check; grading always targets that namespace
# regardless of what NAMESPACE this preflight is invoked with.
if [[ "$NS" != "$GRADED_NS" ]]; then
  fail "namespace mismatch. Requested namespace '$NS' (\$NAMESPACE) does not match the namespace tasks/common/ledger-read-facade/task.yaml actually grades ('$GRADED_NS'). Unset NAMESPACE or set it to '$GRADED_NS'."
fi

if ! iso_resource_exists deployment "$DEPLOY" "$NS"; then
  fail "fixture ABSENT. deployment/$DEPLOY does not exist in namespace $NS. Run scripts/isorun/seed/ledger-read-facade.sh first, or run.sh without --no-seed."
fi

readonly_root="$(kubectl get deployment "$DEPLOY" -n "$NS" \
  -o jsonpath='{.spec.template.spec.containers[0].securityContext.readOnlyRootFilesystem}')"
if [ "$readonly_root" != "true" ]; then
  fail "fixture MALFORMED. readOnlyRootFilesystem='${readonly_root}', expected 'true'. Re-seed with scripts/isorun/seed/ledger-read-facade.sh."
fi

empty_dir_count="$(kubectl get deployment "$DEPLOY" -n "$NS" \
  -o jsonpath='{.spec.template.spec.volumes[?(@.emptyDir)].name}' | wc -w | tr -d ' ')"
if [ "$empty_dir_count" != "0" ]; then
  fail "ALREADY FIXED, re-seed. deployment/$DEPLOY already has ${empty_dir_count} emptyDir volume(s) mounted before the agent ran. Re-seed with scripts/isorun/seed/ledger-read-facade.sh before this run."
fi

netpol_count="$(kubectl -n "$NS" get networkpolicy -o name | wc -l | tr -d ' ')"
if [ "$netpol_count" != "0" ]; then
  fail "ALREADY FIXED, re-seed. namespace $NS already has ${netpol_count} NetworkPolicy object(s) before the agent ran. Re-seed with scripts/isorun/seed/ledger-read-facade.sh before this run."
fi

echo "PREFLIGHT OK [ledger-read-facade]: facade crashlooping (no writable mounts), no netpol/pdb yet"
