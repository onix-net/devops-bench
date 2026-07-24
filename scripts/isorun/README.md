# scripts/isorun

Helper scripts that launch a single devops-bench task from an **isolated
workspace**, so the agent can't reach this repo (the answer keys under
`solutions/`, the `task.yaml`, or the verifier code): the harness itself is
invoked via `uv run --project "$REPO" ...` from a scratch directory outside
the repo, so the agent subprocess inherits that scratch cwd as its only path
back to anything on disk.

Each run under `--no-infra` also runs a per-task cleanup hook first, so a
re-run starts from a clean slate instead of colliding with whatever the
previous run left behind. Under the default provisioning path, tofu owns
bringup and teardown instead, so there is no shell cleanup hook to run.

## Fast local iteration: stand up once, then iterate

Every tofu stack under `tf/prebuilt/` creates its own run-scoped cluster and
cannot seed into a cluster that already exists. That is correct for a real
graded run, but it makes fast iteration painful: every provisioning run (the
default, or explicit `--infra`) pays for a fresh cluster build just to test a
one-line change to a task's fixture or prompt.

For fast iteration against an **already-standing** cluster, five tasks bypass
tofu entirely under `--no-infra`: `fix-config`, `deploy-config`, and
`optimize-scale` (GKE-backed), plus `ledger-read-facade` and
`checkout-multi-service-outage` (kind-backed, against a standing cluster
built from their own dedicated `tf/prebuilt/ledger-read-facade-kind` and
`tf/prebuilt/checkout-multi-service-outage-kind` stacks, each of which
installs `tf/modules/ingress-nginx` directly):

1. Stand up a cluster once, by hand or with a one-off `tofu apply` of the
   matching stack, and export `CLUSTER` / `PROJECT` / `REGION` / `NAMESPACE`
   for it.
2. Run `scripts/isorun/run.sh <task.yaml> gemini --no-infra` repeatedly. Each
   run applies the task's fixture directly with `kubectl` (the seed hook),
   asserts it landed in the exact broken pre-state the task's
   `verification_entries` expect (the preflight guard), and only then
   launches the agent against the standing cluster.
3. Iterate on the task, the fixture, or the agent config in seconds, with no
   tofu apply/destroy cycle in the loop.

This only works for tasks that have both a `seed/` and (ideally) a
`preflight/` script; every other task still needs the default provisioning
path (or a manually seeded cluster) if run with `--no-infra`.

## Usage

```bash
# gemini agent, default mode: provisions infra via tofu (tofu seeds the
# fixture during bringup) and tears it down at the end
scripts/isorun/run.sh tasks/gcp/fix-config/task.yaml gemini

# gemini agent, --no-infra fast-iteration loop against an already-standing
# cluster: seed + preflight run automatically for fix-config/deploy-config/
# optimize-scale/ledger-read-facade/checkout-multi-service-outage
scripts/isorun/run.sh tasks/gcp/fix-config/task.yaml gemini --no-infra

# openclaw (oc) agent, --infra passed explicitly: a no-op alias, since
# provisioning is already the default
scripts/isorun/run.sh tasks/common/cve-remediation/task.yaml oc --infra

# keep the scratch workspace around afterward for inspection
scripts/isorun/run.sh tasks/common/optimize-scale/task.yaml gemini --keep

# run against whatever is already on the cluster, unchecked: skip seed AND preflight
scripts/isorun/run.sh tasks/gcp/deploy-config/task.yaml gemini --no-infra --no-seed
```

`gemini` is the default agent if omitted. Provisioning is the default mode:
with no infra flag, `run.sh` provisions infra during bringup (`tofu apply`)
and tears it down at the end, exactly like a plain `python -m devops_bench`
run without `--no-infra`. The primary agent model defaults to
`gemini-3.5-flash` (override with `AGENT_MODEL`); the judge defaults to
`gemini-3.1-pro-preview` (override with `JUDGE_MODEL`), regardless of which
agent is under test. The per-task agent timeout defaults to 1800 seconds
(override with `AGENT_TIMEOUT_SEC`).

## `--no-infra` vs `--infra`

Provisioning is the **default**. With no infra flag, `run.sh` runs a normal
tofu bringup: builds a fresh, run-scoped cluster, lets tofu seed it (for
`ledger-read-facade` and `checkout-multi-service-outage` that means a
`null_resource` applying the fixture during `tofu apply`; see below), runs
the agent, then tears the cluster down, exactly like a plain
`python -m devops_bench` run without `--no-infra`. Under this path the shell
cleanup/seed/preflight hooks in this directory are skipped (tofu already
owns seeding), and so is the kubectl current-context assertion described
below, since there is no pre-existing cluster to assert against; the run
creates its own.

`--infra` is accepted as an explicit, **no-op alias** for the default: pass
it if you want the mode spelled out for readability, but it does not change
behavior.

`--no-infra` is the **opt-in fast loop** against an already-standing
cluster. It skips provisioning and reuses whatever cluster is already
configured. Most of these tasks (`deployer: "tofu"`) depend on
tofu-**seeded** cluster state (broken configs, Kyverno policies, bare
GitOps repos, etc.), so `--no-infra` instead drives the
cleanup -> seed -> preflight sequence itself (see below) for any task that
has a `scripts/isorun/seed/<task-name>.sh` hook, and it verifies your
current kubectl context matches `$CLUSTER` before touching anything, since
under this path the cluster already exists and must be the right one.

`run.sh` still prints a prominent warning when you run a tofu-backed task
with `--no-infra` and that task has **no** seed hook, as a reminder to check
the seed is actually there before trusting the result. Tasks with a seed
hook do not print this warning: seeding and its correctness are handled by
the seed and preflight steps instead. `--no-infra --no-seed` skips the seed
and preflight hooks too, but the kubectl context assertion still runs (see
[`--no-seed`](#--no-seed) below).

## Cleanup hooks

Under `--no-infra` (and without `--no-seed`), `run.sh` looks for
`scripts/isorun/cleanup/<task-name>.sh` (keyed off the task's directory
name, e.g. `cve-remediation` for `tasks/common/cve-remediation/task.yaml`)
and runs it as a pre-run reset. Each hook is idempotent (safe to run when
nothing exists yet) and only deletes what that task creates; it leaves
tofu-owned/tofu-destroyed resources (the cluster, Secret Manager secrets,
the Lustre instance, etc.) alone. Under the default provisioning path, or
with `--no-seed`, this step is skipped: tofu owns seeding during bringup and
teardown, so there is nothing for the shell hook to reset.

## Fixtures, seed hooks, and preflight guards

These three directories only exist for the tasks in the fast-iteration loop
(`fix-config`, `deploy-config`, `optimize-scale`, `ledger-read-facade`,
`checkout-multi-service-outage`); other tasks are unaffected and behave
exactly as before.

- **`fixtures/<task-name>.yaml`**: standalone, kubectl-appliable manifests
  that recreate a tofu stack's in-cluster pre-agent state, for `fix-config`
  and `optimize-scale`. Each file's header comment states which tofu stack
  and `seed_mode` it was derived from. These are **hand-maintained copies
  for fast local iteration, not generated artifacts**: tofu remains the
  source of truth for real graded runs, and a fixture can silently drift out
  of sync if the tofu stack changes and the fixture isn't updated to match.
  `deploy-config` has no fixture file of its own; its only seeded object (a
  Workload Identity ServiceAccount) is small enough to inline in its seed
  script. `ledger-read-facade` and `checkout-multi-service-outage` don't use
  this directory at all: their fixtures live at
  `tf/prebuilt/<task>-kind/manifests/<task>.yaml`, a single source of truth
  applied both by their dedicated tofu stack (via a `null_resource` during
  `tofu apply`) and by their `scripts/isorun/seed/<task-name>.sh` hook, so
  there's no copy to drift out of sync.

- **`seed/<task-name>.sh`**: runs after the cleanup hook, unless `--no-seed`
  is passed. Idempotent: resets whatever a previous run left behind, then
  applies the fixture with `kubectl apply` (never `create`) so the broken
  pre-state exists. Reads `CLUSTER` / `PROJECT` / `REGION` / `NAMESPACE` from
  the environment.

- **`preflight/<task-name>.sh`**: runs after the seed hook, unless
  `--no-seed` is passed. Asserts the fixture is present **and still in the
  exact broken shape** the task's `verification_entries` grade, so an agent
  never runs against a cluster that would score a pass for free (an
  already-fixed fixture, a missing prerequisite, a stale leftover object,
  etc). Exits nonzero with a specific, loud message on any mismatch, which
  **aborts the run** before the agent is launched.

Under `ISORUN_DRYRUN=1`, both the seed and preflight steps only print what
they would do; they do not touch the cluster.

## `--no-seed`

Pass `--no-seed` to skip both the seed and the preflight hooks and run the
agent against whatever is already on the cluster, unchecked. Use this when
you deliberately want to test against custom or partially-modified cluster
state rather than the canonical fixture.

## Auth

Both agents authenticate via Vertex ADC: no API keys. `iso_auth_gemini` and
`iso_auth_oc` in `_common.sh` unset every `*_API_KEY` env var and export the
`GOOGLE_GENAI_USE_VERTEXAI` / `GCP_PROJECT_ID` / `GCP_VERTEX_LOCATION=global`
triad the agent and judge each read. `oc` additionally needs the
`GOOGLE_CLOUD_API_KEY=gcp-vertex-credentials` ADC marker and may need a one-time
`oc exec-policy preset yolo` before it will run tool calls unattended.

## Dry run

Set `ISORUN_DRYRUN=1` to print the `uv run ...` command `run.sh` would launch
(and the scratch workspace it would `cd` into) without actually running it.
