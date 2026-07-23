#!/usr/bin/env bash
# Launches one devops-bench task from an isolated scratch workspace, after
# running the task's pre-run cleanup hook (if any).
#
# Usage: run.sh <task.yaml-path> [gemini|oc] [--no-infra|--infra] [--keep]
set -euo pipefail

usage() {
  cat <<'USAGE' >&2
Usage: run.sh <task.yaml-path> [gemini|oc] [--no-infra|--infra] [--keep]

  <task.yaml-path>  Path to a task.yaml, absolute or relative to the repo root.
  gemini|oc         Agent to run (default: gemini).
  --no-infra        Skip infra provisioning; reuse the ambient cluster (default).
  --infra           Provision infra via tofu (required for tofu-seeded tasks).
  --keep            Do not delete the scratch workspace on exit.
USAGE
}

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 1
fi

TASK_ARG="$1"; shift
AGENT="gemini"
MODE="--no-infra"
KEEP=0

for arg in "$@"; do
  case "$arg" in
    gemini|oc) AGENT="$arg" ;;
    --no-infra|--infra) MODE="$arg" ;;
    --keep) KEEP=1 ;;
    *)
      echo "run.sh: unknown argument: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/isorun/_common.sh
source "$SCRIPT_DIR/_common.sh"

if [[ "$TASK_ARG" = /* ]]; then
  TASK_PATH="$TASK_ARG"
else
  TASK_PATH="$REPO/$TASK_ARG"
fi

if [[ ! -f "$TASK_PATH" ]]; then
  echo "run.sh: task file not found: $TASK_PATH" >&2
  exit 1
fi

TASKNAME="$(basename "$(dirname "$TASK_PATH")")"

echo "==> Task: $TASKNAME ($TASK_PATH)"
echo "==> Agent: $AGENT, mode: $MODE"

# Special-case the NAMESPACE for stacks with a non-default one; computed here
# so both the cleanup hook (below) and the harness invocation see it.
case "$TASKNAME" in
  secret-rotation) NAMESPACE="${NAMESPACE:-secret-rotation}" ;;
  cp-recovery) NAMESPACE="${NAMESPACE:-cp-recovery}" ;;
  migration-and-upgrade) NAMESPACE="${NAMESPACE:-migration}" ;;
  spot-rebalancing) NAMESPACE="${NAMESPACE:-apps}" ;;
  *) ;;
esac

CLEANUP_HOOK="$SCRIPT_DIR/cleanup/$TASKNAME.sh"
if [[ -f "$CLEANUP_HOOK" ]]; then
  if [[ "${ISORUN_DRYRUN:-0}" == "1" ]]; then
    echo "[dry-run] would run cleanup: $CLEANUP_HOOK"
  else
    echo "==> Running pre-run cleanup hook: $CLEANUP_HOOK"
    CLUSTER="$CLUSTER" PROJECT="$PROJECT" REGION="$REGION" NAMESPACE="${NAMESPACE:-}" "$CLEANUP_HOOK"
  fi
else
  echo "==> No cleanup hook for task '$TASKNAME'; skipping pre-run reset."
fi

if [[ "$MODE" == "--no-infra" ]] && grep -Eq 'deployer:[[:space:]]*"tofu"' "$TASK_PATH"; then
  cat <<WARN >&2
############################################################
WARNING: task '$TASKNAME' uses deployer: "tofu" and depends on
tofu-SEEDED cluster state (broken configs, Kyverno policies, bare
GitOps repos, etc). --no-infra will NOT seed that state; it only
reuses the ambient cluster. If the seed isn't already present,
re-run with --infra or seed the stack manually before continuing.
############################################################
WARN
fi

if [[ -n "${NAMESPACE:-}" ]]; then
  export NAMESPACE
fi

case "$AGENT" in
  gemini) iso_auth_gemini ;;
  oc) iso_auth_oc ;;
esac

export GKE_CLUSTER_NAME="$CLUSTER"
export AGENT_TIMEOUT_SEC="${AGENT_TIMEOUT_SEC:-1800}"

RESULTS_ROOT="$REPO/results/iso-$TASKNAME"
CMD=(uv run --project "$REPO" python -m devops_bench "$MODE" --project "$PROJECT" --cluster "$CLUSTER" --results-root "$RESULTS_ROOT" "$TASK_PATH")

WS="$(iso_stage_ws)"
if [[ "$KEEP" -eq 0 ]]; then
  trap 'rm -rf "$WS"' EXIT
fi

echo "==> Isolated workspace: $WS"
echo "==> Results root: $RESULTS_ROOT"

if [[ "${ISORUN_DRYRUN:-0}" == "1" ]]; then
  echo "==> [dry-run] would cd to $WS and run:"
  printf '%q ' "${CMD[@]}"
  echo
else
  cd "$WS"
  "${CMD[@]}"
fi

echo "==> Results: $RESULTS_ROOT"
echo "==> Audit reminder: confirm the agent actually WROTE files / kubectl reported 'created' or 'configured' before trusting a pass."
