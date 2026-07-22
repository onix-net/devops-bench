# scripts/isorun

Helper scripts that launch a single devops-bench task from an **isolated
workspace**, so the agent can't reach this repo (the answer keys under
`solutions/`, the `task.yaml`, or the verifier code): the harness itself is
invoked via `uv run --project "$REPO" ...` from a scratch directory outside
the repo, so the agent subprocess inherits that scratch cwd as its only path
back to anything on disk.

Each run also runs a per-task cleanup hook first, so a re-run starts from a
clean slate instead of colliding with whatever the previous run left behind.

## Usage

```bash
# gemini agent, default --no-infra (reuse the ambient cluster)
scripts/isorun/run.sh tasks/gcp/fix-config/task.yaml gemini --no-infra

# openclaw (oc) agent, force tofu provisioning
scripts/isorun/run.sh tasks/common/cve-remediation/task.yaml oc --infra

# keep the scratch workspace around afterward for inspection
scripts/isorun/run.sh tasks/common/optimize-scale/task.yaml gemini --keep
```

`gemini` is the default agent if omitted, and `--no-infra` is the default
mode. The primary agent model is `gemini-3.5-flash`; the judge is held at
`gemini-3.1-pro-preview` regardless of which agent is under test.

## `--no-infra` vs `--infra`

Most of these tasks (`deployer: "tofu"`) depend on tofu-**seeded** cluster
state: broken configs, Kyverno policies, bare GitOps repos, etc. `--no-infra`
skips provisioning and reuses whatever cluster is already configured — it
does **not** seed that state. If the seed isn't already present (e.g. a fresh
cluster, or one that was already cleaned up), you need `--infra` to actually
provision and seed the stack, or you must seed it manually first.

`run.sh` prints a prominent warning when you run a tofu-backed task with
`--no-infra`, as a reminder to check the seed is actually there before
trusting the result.

## Cleanup hooks

Before launching, `run.sh` looks for `scripts/isorun/cleanup/<task-name>.sh`
(keyed off the task's directory name, e.g. `cve-remediation` for
`tasks/common/cve-remediation/task.yaml`) and runs it as a pre-run reset. Each
hook is idempotent — safe to run when nothing exists yet — and only deletes
what that task creates; it leaves tofu-owned/tofu-destroyed resources (the
cluster, Secret Manager secrets, the Lustre instance, etc.) alone.

## Auth

Both agents authenticate via Vertex ADC — no API keys. `iso_auth_gemini` and
`iso_auth_oc` in `_common.sh` unset every `*_API_KEY` env var and export the
`GOOGLE_GENAI_USE_VERTEXAI` / `GCP_PROJECT_ID` / `GCP_VERTEX_LOCATION=global`
triad the agent and judge each read. `oc` additionally needs the
`GOOGLE_CLOUD_API_KEY=gcp-vertex-credentials` ADC marker and may need a one-time
`oc exec-policy preset yolo` before it will run tool calls unattended.

## Dry run

Set `ISORUN_DRYRUN=1` to print the `uv run ...` command `run.sh` would launch
(and the scratch workspace it would `cd` into) without actually running it.
