# Control Plane Recovery Task

This task evaluates the agent's ability to diagnose and recover a corrupted etcd control
plane on a **real Kubernetes cluster**. Unlike a managed control plane (e.g. GKE) which hides
etcd and the API server, this task runs on a multi-node [kind](https://kind.sigs.k8s.io/)
cluster whose **real** 3-member etcd and API server we fully control.

The agent must: diagnose the unhealthy etcd member, verify the integrity of a staged etcd
snapshot, restore the member and re-establish Raft quorum, reconcile the running workloads
against the desired GitOps state, and produce an incident report.

## How it works

- **Infrastructure** (`tf/prebuilt/cp-recovery-kind`) is provisioned by OpenTofu when you run
  the evaluator. It creates a kind cluster with **3 control-plane nodes** (a real 3-member
  stacked etcd) and **1 worker**, deploys the desired-state workloads (`workload-1`,
  `workload-2`), the `gitops-state` ConfigMap, and a backup volume (`etcd-backup-pvc`).
- **Fault injection happens outside the cluster.** During `tofu apply`,
  `scripts/inject-fault.sh` takes a verified etcd snapshot (staging it + its sha256 into the
  backup PVC), then corrupts a **single** etcd member and restarts it. Quorum (2/3) is
  preserved, so the API server stays up and the agent keeps `kubectl` access — but one member
  crash-loops. No Job, ConfigMap, or script describing the corruption is left in the cluster.
- **`workload-3`** is intentionally never created, so after recovery the agent must reconcile
  it from the `gitops-state` desired state.

## Setup & Running the Benchmark

Because kind runs the cluster as local Docker containers, the eval, the kind cluster, and the
agent must all run on the **same host**. The simplest way is to run everything directly on the
runner VM.

### 1. Prepare the host (run the eval on the runner VM)

SSH into the runner VM, clone this repo, and make sure these are installed and on `PATH`:

- Docker (running)
- [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- `kubectl`
- `tofu` (OpenTofu)
- the `oc` (OpenClaw) agent binary at `~/bin/oc` (override with `OPENCLAW_BIN`)

> The VM needs enough CPU/RAM/disk for a 4-node kind cluster (3 control-plane + 1 worker).

### 2. Export Environment Variables

```bash
# Cluster / namespace. CLUSTER_NAME becomes the kind cluster name.
export GKE_CLUSTER_NAME="cp-recovery-kind"     # used as the kind cluster name
export NAMESPACE="cp-recovery"
# Required by the evaluator for prompt substitution / Vertex judge. When using API
# keys (below) this can be any placeholder value.
export GCP_PROJECT_ID="local-kind"

# Run the OpenClaw agent locally (no SSH to a GCE VM).
export OPENCLAW_LOCAL="true"

# Agent Config
export BENCH_AGENT_TYPE="cli"
export AGENT_TARGET="oc"
export AGENT_PROVIDER="google"
export AGENT_MODEL="gemini-3.1-pro-preview"
export AGENT_API_KEY="your-gemini-api-key"

# Judge Config
export JUDGE_PROVIDER="google"
export JUDGE_MODEL="gemini-3.1-pro-preview"
export JUDGE_API_KEY="your-gemini-api-key"
```

### 3. Run the Evaluator

```bash
python3 pkg/evaluator/evaluate.py complextasks/cp-recovery/task.yaml
```

> [!TIP]
> **Saving time on subsequent runs:** export `BENCH_NO_TEARDOWN="true"` to keep the kind
> cluster between runs. To re-run cleanly, tear down and recreate with a fresh namespace:
> `tofu -chdir=tf/prebuilt/cp-recovery-kind destroy` (or `kind delete cluster --name "${GKE_CLUSTER_NAME}"`).

## Verifying the environment manually

After provisioning (or `tofu -chdir=tf/prebuilt/cp-recovery-kind apply`):

```bash
kubectl get nodes                                   # 3 control-plane + 1 worker
kubectl -n kube-system get pods -l component=etcd   # one etcd-* CrashLoopBackOff
kubectl get deploy -n "${NAMESPACE}"                # workload-1, workload-2 (no workload-3)
kubectl get pvc -n "${NAMESPACE}" etcd-backup-pvc   # Bound; holds etcd-backup.db + .sha256
kubectl get ns                                       # still works -> API server up (quorum held)
```
