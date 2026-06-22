# devops-bench: project and staffing plan

_Wave 1 ships ~115 tasks in 6 to 8 weeks across a two-plane taxonomy: a Kubernetes plane and a focused, deep GCP Cloud plane, plus the cloud-in-k8s seam._
_This document is both an internal execution plan (owners, waves, velocity, RACI, definition of done) and a buy-in brief for Google leadership._

Status: this operationalizes `TASK_CATALOG_BRAINSTORM.md`.

## Table of contents

1. [Executive summary](#executive-summary)
2. [The two-plane taxonomy and Wave 1 allocation](#the-two-plane-taxonomy-and-wave-1-allocation)
3. [Staffing and operating model](#staffing-and-operating-model)
4. [Platform and harness workstream](#platform-and-harness-workstream)
5. [Benchmark integrity: making tasks hard to game](#benchmark-integrity-making-tasks-hard-to-game)
6. [Execution plan: the 6-8 week sprint and the later-wave roadmap](#execution-plan-the-6-8-week-sprint-and-the-later-wave-roadmap)
7. [Risks, dependencies, open decisions, and docs](#risks-dependencies-open-decisions-and-docs)

---

## Executive summary

### What this is

`devops-bench` is a benchmark that scores AI agents on real DevOps work. Instead of static prompts or multiple-choice, it provisions live infrastructure just-in-time, hands the agent a task, lets it act against the real control plane, and then checks the result. The premise is simple: the only honest way to know whether an agent can run a platform is to make it run one and inspect what it did.

### The change in one line

We are adding a first-class **Cloud plane** to the benchmark and shipping **~115 tasks in 6 to 8 weeks** with a tiny, AI-fluent team, by replacing hand-authoring with an authoring factory and grounding scoring in deterministic resource facts. Wave 1 goes smaller and deeper: a focused GCP and Kubernetes slice rather than thin breadth, with multicloud deliberately deferred.

### Where we are today

The honest baseline is small and lopsided:

| Dimension | Today |
| --- | --- |
| Total tasks | 14 (`tasks/gcp/` x13, `tasks/generic/` x1) |
| Cloud/k8s share | ~93% GCP/Kubernetes; non-k8s cloud surface is essentially absent |
| Scoring | 100% GEval (LLM-as-judge via `deepeval`) |
| Deterministic verifiers | 2 only: `PodHealthyVerifier`, `ScalingCompleteVerifier` (in `pkg/agents/verifier/spec.py`) |
| Terraform stacks | 4 GCP + 2 kind under `tf/prebuilt/`; no AWS/Azure |
| Test CI | None (only a Pages deploy workflow) |

Wave 1 is roughly 93% greenfield. That is the opportunity, not just the gap.

### The bet

We are betting on three things, in this order:

1. **Deterministic outcome scoring over LLM-judge.** We score on whether resources exist and whether they are configured correctly, not on a model's opinion of a transcript. We get there by extending the existing verifier framework (a new resource-existence verifier and a resource-configuration verifier, registered in `spec.py`) and reusing the current `gcli`/`openclaw` execution path. We are deliberately **not** building the speculative black-box runner.
2. **Two planes, not one.** A Kubernetes plane (cloud-agnostic, kind-based) and a Cloud plane (no cluster required), with a seam that weaves cloud-specific behavior into Kubernetes. This is the direct answer to the catalog drifting too k8s-heavy and losing sight of cloud.
3. **A factory, not artisans.** Agents mass-author each task as a generator plus a parameterized verifier, and an automated gate validates every one across sampled parameterizations: apply the oracle end-state and all checks must PASS; apply only the seeded baseline and they must FAIL. That gate is what lets a tiny team move at ~15-20 landed tasks/week.

> **Decisions locked**
> 1. **Staffing.** Human-owned workstreams executed by an agent fleet. Eric is DRI/architect; 2 engineers; no headcount boxes.
> 2. **Timeline.** Wave 1 (~115 tasks) lands in 6 to 8 weeks, foundation front-loaded into a two-week phase.
> 3. **Cloud rebalance.** Add a first-class Cloud plane; keep the k8s backbone; AWS/Azure parity phased to later waves.
> 4. **Audience.** One document serving both internal execution and a Google leadership pitch.
> 5. **Scoring.** Lightweight deterministic verifiers on resource existence/config; oracle-PASS/baseline-FAIL gate; no black-box runner; contract matched loosely so a Google foundation can swap in.
> 6. **Taxonomy.** The two-plane reframe (Kubernetes + Cloud + the cloud-in-k8s seam) is the organizing spine.
> 7. **Wave 1 size.** Re-scope to ~115 logical tasks, smaller and deeper on GCP/k8s; trim the k8s share to make room for cloud, drop multicloud from Wave 1.
> 8. **Integrity.** Commit four anti-gaming mechanisms (parametric task generation, out-of-band scoring, root-cause randomization, and a proactive/diagnosis-heavy scored set with no-op and trap tasks) into the Wave 1 foundation; keep four others (behavioral checks, blast-radius invariants, multi-fault composition, transcript-tell detection) designed but not committed; treat a private hold-out of task families as a separate discussion with Google with a known limitation. The durable defense is run-time diagnosis, not secrecy.

The rebalance, in one number: cloud-facing content is now ~30 (plane) + ~17 (seam) = ~47 of 115, roughly 40% of the catalog, up from ~6 today.

### What the investment buys (for Google)

This is a small, contained bet with leverage well beyond its cost:

- **A defensible standard.** A reproducible benchmark Google can anchor to, with deterministic outcome scoring grounded in resource facts rather than LLM-as-judge. Same end-state, same score, every run.
- **Credible neutrality.** Two planes, GCP-first with AWS/Azure parity on a contained abstraction (the cloud cred-fetch in `TFDeployer` is the one seam to generalize, not a rewrite). Broad coverage makes GKE/GCP strengths legible without looking partisan.
- **Hard to game, hard to contaminate.** A benchmark that is parametric (fresh instance each run, no fixed answer to memorize) and scores out-of-band (the agent never sees the oracle or the verifier) is resistant to teach-to-the-test and training-data contamination. The durable integrity comes from tasks that require run-time diagnosis (root-cause randomization plus a proactive- and diagnosis-heavy set), so a high score reflects competence rather than taxonomy recall, with a private hold-out as a secondary layer to be worked out with Google. That integrity is exactly what makes a "neutral standard" credible rather than a leaderboard to overfit.
- **Cheap scale.** The authoring factory grows the catalog from 14 to ~115 now, and toward ~270-300 cases across AWS and Azure in later waves, with the same tiny team. The marginal cost of the next task is an agent run plus a human spot-check, not a week of engineering.

The single biggest risk is velocity: 14 to 115 in 6 to 8 weeks is aggressive and rests on the factory and the quality gate holding. We mitigate it by staffing the scoring foundation first, keeping it deliberately thin, and proving the loop on free kind-based k8s tasks before we spend a dollar of cloud budget. The smaller scope plus the full 8-week runway materially de-risk it.

---

## The two-plane taxonomy and Wave 1 allocation

Today the catalog is 14 tasks: 13 GCP-specific under `tasks/gcp/` and 1 k8s-generic case (`tasks/generic/gateway-https-redirect`). Read by intent rather than by directory, only about 6 of those exercise the cloud platform as a first-class surface; the rest are Kubernetes work that happens to run on GKE. That is the concrete shape of "we lost sight of cloud": the cloud-platform surface is essentially a rounding error.

Wave 1 fixes the balance directly. We hold the catalog at ~115 logical tasks, trim the Kubernetes share to make room, and stand up a first-class Cloud plane that goes deep on a focused GCP slice rather than thin across all twelve categories. After Wave 1 the Cloud plane is 30 tasks, with a further 17-task seam where cloud-specific behavior lives inside Kubernetes. Cloud-facing content therefore moves from ~6 tasks to roughly 47 of 115, about 40% of the catalog instead of a corner of it.

The organizing spine is two planes plus a seam:

- **Plane 1, Kubernetes**: cloud-agnostic, kind-based backbone. The cluster is the system under test.
- **Plane 2, Cloud platform**: no cluster required. The cloud control plane is the system under test. GCP-first in Wave 1, deep on a focused slice, with AWS/Azure analogs phased to later waves.
- **The seam**: cloud-specific bits that only exist because Kubernetes is running on a cloud (Workload Identity, cloud LoadBalancers, cloud StorageClasses). GCP-first in Wave 1; the GKE/EKS/AKS matrix expansion is a later wave.

### Plane 1: Kubernetes (target 68)

Cloud-agnostic, runs on kind, so the authoring loop is free and fast. This is why the k8s plane goes first in the factory.

| Cat | Category | Wave-1 count |
| --- | --- | --- |
| 1 | Rollout, progressive delivery & rollback | 6 |
| 2 | Scheduling, bin-packing & right-sizing | 6 |
| 3 | Autoscaling (HPA/KEDA/cluster-autoscaler), k8s portion | 4 |
| 4 | Workload crash & pod lifecycle remediation | 7 |
| 5 | Storage, volumes & disk-pressure, k8s portion | 4 |
| 6 | Stateful recovery & DR, k8s portion | 3 |
| 7 | Cluster networking (DNS/Services/LB), k8s portion | 4 |
| 8 | NetworkPolicy, RBAC & admission guardrails | 5 |
| 9 | Secrets, TLS & cert lifecycle, k8s portion | 4 |
| 10 | Supply chain (provenance/signing/CVE), k8s portion | 3 |
| 11 | GitOps & IaC drift, k8s portion | 4 |
| 13 | Spot resilience & chaos, k8s portion | 4 |
| 14 | Observability & SLOs, in-cluster portion | 4 |
| 15 | GPU & AI inference platform ops, k8s portion | 3 |
| 16 | Database & stateful-data, in-cluster portion | 2 |
| 17 | Service mesh & L7 traffic management | 5 |
| | **Sum, Plane 1** | **68** |

### Plane 2: Cloud platform (target 30)

No cluster required. GCP-first in Wave 1, and deliberately deep on a focused slice of 7 categories rather than thin across all twelve. Each category has AWS and Azure analogs queued for later waves. These tasks cost real cloud resources to validate, so they run against ephemeral sandboxes with tight teardown.

| ID | Category | Count | Example tasks |
| --- | --- | --- | --- |
| C4 | Identity, IAM & org governance (service accounts/roles/WIF/Org Policy/KMS) | 6 | GitHub Actions OIDC to GCP via Workload Identity Federation is failing; an Org Policy constraint blocks a legitimate deploy; rotate a KMS key without breaking decryption |
| C3 | Cloud networking (VPC/subnets/routes/peering/Cloud NAT/PSC/firewall, non-k8s LB) | 5 | Two VPCs cannot talk after peering due to overlapping CIDR or a missing route; a Private Service Connect endpoint cannot resolve |
| C2 | Managed data services (Cloud SQL/Spanner/BigQuery/Memorystore) | 5 | Point-in-time-restore a Cloud SQL instance after bad data; fix a read-replica lag that is blowing the RPO; a BigQuery scheduled query silently fails on a permissions change |
| C1 | Serverless & app platforms (Cloud Run/Functions/App Engine) | 4 | Cloud Run service 403s because the invoker IAM binding is missing; a Function times out on a VPC-connector cold start |
| C10 | Cloud security posture (SCC/CSPM/public exposure/encryption-at-rest) | 4 | Remediate a public-exposure finding without an outage; enforce CMEK on a non-compliant resource |
| C6 | Object/block storage & data lifecycle (GCS buckets/lifecycle/versioning/retention/public-access) | 3 | A bucket is world-readable, lock it down without breaking the app; a lifecycle rule is deleting data it should not |
| C11 | Cloud IaC & provisioning safety (OpenTofu plan/drift/import/destructive-change guard) | 3 | A `tofu plan` shows a destructive replacement, explain why and make it non-destructive; import an out-of-band-created resource into state |
| | **Sum, Plane 2** | **30** | |

Note: the deferred Cloud-plane categories (C5 VM compute, C7 FinOps, C8 cloud observability, C9 messaging, C12 DNS/edge/CDN) move to a later wave. Wave 1 goes deep on a focused slice rather than thin across all twelve.

### The seam: cloud-specific bits inside Kubernetes (target 17)

These are Kubernetes tasks whose difficulty comes from the cloud underneath. GCP-first in Wave 1. Representative cases:

- Workload Identity for a pod to read a cloud secret with no mounted credential.
- Internal LoadBalancer with a static IP via the right annotation dialect.
- Default StorageClass / PVC binding on a fresh cluster.
- A CoreDNS stub zone that survives an upgrade.
- A NetworkPolicy that is actually enforced by the CNI, not just applied.
- A GPU/spot node pool with a tolerating workload.
- API-server audit logging to find who deleted a Deployment.

Sum, seam: **17**.

### Wave 1 totals

| Bucket | Wave-1 count |
| --- | --- |
| Plane 1: Kubernetes | 68 |
| Plane 2: Cloud platform | 30 |
| The seam: cloud-specific-in-k8s | 17 |
| **Total** | **115** |

Multicloud is deliberately deferred out of Wave 1 because it is the most expensive to provision and the least deterministic. The GKE/EKS/AKS matrix expansion of the seam, the AWS/Azure analogs of Plane 2, and the thin multicloud slice are all out of Wave 1; they land in later waves once the deployment-target abstraction exists.

### Mode and difficulty targets (Wave 1)

- **Interaction mode**: roughly proactive-detection 50%, instructed 30%, diagnosis-report 20%. We bias toward proactive-detection because it is inherently the hardest format to game (the agent must notice the problem from signals, not be told the fix). No-op and trap scenarios live within the proactive-detection share. The diagnosis-report share stays capped until the structured-claim verifier lands.
- **Difficulty**: roughly simple 60%, complex 40%.

---

## Staffing and operating model

We run this as a tiny, AI-fluent team where the workforce is an agent fleet, not headcount. Three people own workstreams and quality; the agents do the bulk authoring. The model only works because the validation gate (oracle PASS, baseline FAIL) lets humans review for realism instead of plumbing.

### The four roles

**DRI / Architect (Eric)**
- Owns the two-plane taxonomy, the Wave 1 allocation (68 k8s, 30 cloud, 17 seam), and sequencing.
- Owns the quality bar, the verifier design patterns, and the review gates.
- Designs category templates and reviews agent output. Does not hand-author tasks.
- Owns the Google narrative and the open decisions still to settle.

**Engineer 1: Platform / Harness owner**
- Owns the lightweight deterministic scoring foundation: resource-existence and resource-configuration (jsonpath/comparator) verifiers, registered in `pkg/agents/verifier/spec.py`. No black-box runner.
- Owns parametric task generation (a task becomes a generator plus a parameterized verifier) and out-of-band scoring (the agent never sees the oracle or the verification spec). This is why the foundation now spans weeks 1-2.
- Owns the validation harness (oracle PASS / baseline FAIL across sampled parameterizations) and CI, which must be built from scratch.
- Owns the structured-claim verifier that unlocks diagnosis-report mode, plus chaos and metric-seeding reuse.
- Later: the deployment-target abstraction that unlocks AWS and Azure.

**Engineer 2: Cloud-plane owner**
- Owns the Cloud plane (the focused 7-category GCP slice) and the seam: GCP-first terraform stacks and cloud-resource verifiers (`gcloud` / cloud-API existence and configuration checks).
- Owns authoring oversight for cloud tasks, where ephemeral spend and teardown discipline matter most.
- Later: the GCP to AWS to Azure ports.

**The agent fleet (orchestrated by all three)**
- Mass-authors task generators (a parameterized `task.yaml` + `setup.yaml` + `oracle.yaml` plus a parameterized verifier), verifier specs, terraform stacks, and docs.
- Runs the factory loop against `kind` and ephemeral cloud sandboxes.
- Later: the parity ports across clouds.

### RACI across the main workstreams

| Workstream | DRI/Architect | Eng1 Platform | Eng2 Cloud | Agent fleet |
|---|---|---|---|---|
| Scoring foundation (verifiers, parametric generation, out-of-band scoring, CI) | A | R | C | I |
| k8s authoring (Plane 1, ~68) | A | C | I | R |
| Cloud-plane authoring (Plane 2 + seam, ~47) | A | I | R | R |
| CI / validation harness | C | R | C | I |
| Docs (brief, quickstart, tutorial) | A | C | C | R |
| Google pitch | R/A | I | I | I |

R = responsible, A = accountable, C = consulted, I = informed.

### The authoring factory

The factory is the velocity engine. It is a five-step pipeline:

1. **Pick** a task from the taxonomy backlog (human).
2. **Draft** a generator with an agent: a parameterized `task.yaml` (prompt + `verification_spec`), `setup.yaml` (seeded baseline), and `oracle.yaml` (correct end-state), plus a parameterized verifier that matches. The output is a generator, not a static triplet.
3. **Validate** automatically on `kind` (k8s and seam) or an ephemeral cloud sandbox (cloud plane). The gate must hold across sampled parameterizations: for several random instances, applying the oracle makes all verifiers PASS, and applying only the baseline makes them FAIL.
4. **Spot-check** for realism, difficulty, and no-cheese (can the check pass trivially or by accident).
5. **Land** it and tally toward the wave count.

Step 3 is the load-bearing idea. The oracle-PASS / baseline-FAIL gate is a deterministic quality check that an agent cannot fake: a wrong generator fails the gate before a human ever sees it. That is what makes agent-authoring safe at scale. Humans then spend their review budget on realism and difficulty, not on debugging plumbing. The gate uses only the verifier framework and known manifests. It needs no black-box runner, and we are deliberately not building one. Execution reuses the existing `gcli` / `openclaw` path.

### Velocity math

We go from 14 tasks to ~115 in 6 to 8 weeks. The weeks 1-2 foundation delivers 5-10 k8s generators as proof-of-factory, which count toward the 115 total; the remaining ~90 tasks land across roughly 5 authoring weeks (weeks 2-7), putting the pace at ~18-20 landed tasks per week at the top end, k8s-first because it is free and fast.

| Phase | Output |
|---|---|
| Weeks 1-2 | Foundation: verifiers, parametric generation, out-of-band scoring, CI, validation harness; factory proven on 5-10 k8s generators |
| Weeks 2-4 | k8s plane bulk (~68 on `kind`) |
| Weeks 4-6 | Focused GCP cloud slice (~30) + start the seam |
| Weeks 6-7 | Seam (~17 on GKE) + harden + quality sweep |
| Weeks 7-8 | 3 P0 docs + Google pitch + buffer |

We sequence k8s-first on purpose: `kind` tasks are free and fast, so the cheapest loop proves the factory and absorbs most of the volume. Cloud-plane tasks cost ephemeral cloud resources and need tight teardown, so they follow once the loop is hardened. The critical path is the scoring foundation, then the factory, then all authoring. The foundation now includes parametric generation and out-of-band scoring, which is why it is a two-week phase and why the wave is right-sized at ~115: we trade some breadth for a foundation that is hard to game. If it slips, everything downstream slips with it, so it is staffed first.

---

## Platform and harness workstream

Engineer 1 owns the harness. The team's velocity depends on a deterministic scoring foundation landing in the first two weeks so the authoring factory can build against it. We staff this first and keep it deliberately small. The foundation now spans weeks 1-2 rather than a single week because two integrity mechanisms are built in: parametric task generation and out-of-band scoring. With them, a task becomes a (generator, parameterized verifier) pair rather than a static fixture.

### The scoring decision: lightweight verifiers, no black-box runner

We build a lightweight deterministic scoring foundation grounded in resource existence and configuration facts. We explicitly do **not** build the `OUTCOME_MVP.md` black-box runner. The files that spec describes (`blackbox.py`, `outcome_eval.py`, `resource_exists.py`, `jsonpath_match.py`, `adapters/*.sh`) do not exist today, and we are not creating them. An opaque-subprocess agent contract is more surface area than Wave 1 needs.

Instead we extend the existing verifier framework, which is already extensible: a new verifier is `BaseVerifier` plus a registration in the `SingleVerificationSpec` union in `pkg/agents/verifier/spec.py`, alongside the two that ship today (`PodHealthyVerifier`, `ScalingCompleteVerifier`). We add two:

| Verifier | What it asserts | Mechanism |
| --- | --- | --- |
| Resource-existence | A named resource is present (or absent) in the end-state | Lookup against the cluster or cloud API |
| Resource-configuration | A field on a resource matches an expected value | jsonpath selector + comparator (`eq`, `ne`, `gte`, `lte`, `exists`, `contains`), wildcard paths supported |

These two cover the bulk of Wave 1. "The IAM binding exists," "replicas is gte 3," "the bucket is not world-readable," "the route table contains this CIDR" are all existence or single-field-config assertions.

### Parametric task generation and out-of-band scoring

Two integrity mechanisms are committed into the foundation, which is why it is a two-week phase.

- **Parametric task generation.** The factory emits a generator (randomized namespaces, names, replica counts, CIDRs, which of N plausible misconfigs is injected, which resource is broken) plus a verifier parameterized to match. Same scoring logic, fresh instance each run, no fixed answer to memorize. The schema implication is concrete: a task becomes a (generator, parameterized verifier) pair, not a file triplet.
- **Out-of-band scoring.** The agent receives only the prompt and the live environment. `oracle.yaml` and the `verification_spec` are never exposed to the agent. Cheap to enforce, and it kills the most direct cheese path.

Both are detailed in the [Benchmark integrity](#benchmark-integrity-making-tasks-hard-to-game) section.

### Cloud-resource verification (Plane 2)

The two verifiers extend past Kubernetes to cloud resources via `gcloud` and cloud-API existence and configuration queries. Plane 2 needs assertions on IAM bindings, bucket policies and ACLs, VPC routes and peering, KMS key state, and similar. The configuration verifier's jsonpath + comparator model maps cleanly onto the JSON these APIs already return, so the cloud case is a query backend, not a second verifier design. Engineer 2 owns the cloud terraform stacks and authoring oversight; we own the verifier plumbing that scores them.

### The validation harness and CI

There is no test CI today, only a GitHub Pages deploy workflow. The authoring factory's automated quality gate depends on CI existing, so we build it.

The harness encodes the per-task definition of done as an executable check, run across sampled parameterizations:

- Apply the **oracle** end-state, then run the task's verifiers: all must **PASS**.
- Apply only the seeded **baseline** state, then run the same verifiers: they must **FAIL**.

A task that does not satisfy both halves is not a valid task. This is the deterministic quality gate, and it uses only the verifier framework and known manifests. It does not need the black-box runner. k8s and seam tasks validate on `kind` (free, fast loop); cloud-plane tasks validate in an ephemeral cloud sandbox with tight teardown. We wire this into CI so every authored generator is gated before it lands.

### Supporting items

- **Structured-claim verifier.** Diagnosis-report mode is capped until this lands. It scores a structured agent claim (the agent reports a root cause and remediation as data, not prose) against expected fields. Targeted for Weeks 2-4. Whether we commit to it long-term or convert most diagnosis cases to detect-and-fix is an open decision for Eric.
- **In-cluster metric seeding.** Proactive-detection tasks (roughly 50% of Wave 1) need realistic signal in-cluster for the agent to find. We build a reusable seeding path so authors do not hand-roll metrics per task. It also underpins behavioral checks, a designed-but-not-committed integrity control.
- **Chaos and scenario reuse.** We lean on existing stacks under `tf/prebuilt/` (`cp-recovery-kind`, `gpu-stress-test`, etc.) rather than authoring chaos primitives from scratch.

### Google dependency

A Google-provided scoring foundation may arrive, possibly late and possibly with a different contract. We do not block on it. We build thin and match the eventual contract loosely (existence and configuration facts, deterministic results) so a Google foundation can swap in behind our verifier interface without re-authoring tasks. That is the hedge: useful now, replaceable later.

### Later: deployment-target abstraction (deferred to Wave 2)

AWS and Azure parity needs a deployment-target abstraction, and it is explicitly **not** in Wave 1. The good news is that it is a contained change, not a rewrite, because `TFDeployer` is already cloud-agnostic in its apply/destroy loop. The GCP coupling is localized:

- `deployers/tf/tf_deployer.py` hard-codes a `gcloud container clusters get-credentials` call for non-local clusters.
- `deployers/factory.py` `PROVIDER_RESOLVERS` only knows `{gcp, kind}`.
- The cluster-credential path in the evaluate flow assumes GCP env (`PROJECT_ID`, `CLUSTER_NAME`) and a `gke-mcp` path.

The Wave 2 change: pull the credential fetch out of `TFDeployer` into a per-cloud `CredentialsFetcher`, expand `PROVIDER_RESOLVERS`, and add a `target:` field to `task.yaml` so a task declares its deployment target. That single seam unlocks EKS and AKS ports for the portable task set. We design Wave 1 verifiers to be target-agnostic now so this lands cleanly later, but we write none of it this wave.

---

## Benchmark integrity: making tasks hard to game

There is a core tension at the heart of deterministic scoring: deterministic scoring is reproducible, and reproducible-plus-public is memorizable. A benchmark that always poses the identical scenario and checks the identical field is, over time, something an agent can be taught to pass without ever learning to do the work. Three threat models concern us:

- **Training-data contamination.** Public tasks leak into training corpora; the agent has effectively seen the answer.
- **Teach-to-the-test / cheese.** An aware agent satisfies only the checked fields without really fixing the problem.
- **Overfit-to-check.** The agent optimizes for the specific assertion rather than the underlying outcome.

The strongest gaming vector is none of these: it is a **playbook, or lookup-table, agent**. This is not a real agent at all. It is a table that maps each expected task type to a canned command, reading the parameters straight from the prompt. "If asked to scale, run `kubectl scale deploy A --replicas N`, where `A` and `N` come from the prompt." The defenses we have already committed do not stop this on their own. The table keys on task _type_, not on the instance, so instance randomization is exactly the variation it absorbs (it reads the new name and the new replica count out of the prompt and fills them in). And because it never reasons about the end-state, it never needs to see the oracle or the verifier; out-of-band scoring is irrelevant to it. The central principle follows: the durable defense is to make tasks require **run-time diagnosis**, so that knowing the task type does not hand you the answer. We do not bet integrity on secrecy.

We resolve the tension in design rather than leaving it open. Four controls are committed into the Wave 1 foundation; four more are designed and held ready; a private hold-out is a separate discussion with Google with a known limitation.

### Committed in Wave 1 (built into the foundation)

1. **Parametric task generation.** We keep determinism _given per-run parameters that vary_. The factory emits a generator (randomized namespaces, names, replica counts, CIDRs, which of N plausible misconfigs is injected, which resource is broken) plus a verifier parameterized to match. The scoring logic is the same; the instance is fresh each run; there is no fixed answer to memorize. The schema implication is concrete: a task is a (generator, parameterized verifier) pair, not a file triplet. This is the highest-leverage defense and the reason the foundation is a two-week phase.
2. **Oracle and verifier kept out-of-band.** The agent receives only the prompt and the live environment. `oracle.yaml` and the `verification_spec` are never exposed to the agent. It is cheap to enforce and it kills the most direct cheese path.
3. **Root-cause randomization.** We extend parametric generation so that within a task family the same observable symptom maps to a randomized underlying cause. "Pods are Pending" could be quota exhaustion, a node taint, an oversized resource request, an unbindable PVC, or a bad `nodeSelector`, chosen per run. A single canned fix is wrong most of the time; only an agent that diagnoses the specific cause at run time passes. This is the highest-leverage anti-playbook defense and a natural extension of parametric generation: randomize the diagnosis, not just the parameters.
4. **A proactive- and diagnosis-heavy scored set, with no-op and trap tasks.** We bias the scored set so the prompt does not name the action (proactive-detection and diagnosis dominate). We include no-op / false-alarm tasks where the correct move is to report healthy or to do nothing, and trap tasks where the obvious canned remediation fails or is reverted (for example, a manual scale that an HPA reverts, or that a quota wall rejects). A reflexive playbook fails these; an agent that observes before acting passes.

### Designed, not yet committed (decision-gated fast-follow)

5. **Behavioral checks over config-match.** Assert the outcome property (curl the service through the LB and get a 200; confirm no pod OOMs under load for N minutes) rather than the mechanism (a specific field value). Behavioral assertions are harder to cheese and solution-agnostic, which raises the bar further. They lean on metric-seeding.
6. **Blast-radius negative invariants.** The "did the agent make it worse" check, promoted to a first-class anti-cheese control: fail if siblings were broken, or if scope was widened or resources were deleted to satisfy the literal check.
7. **Multi-fault composition.** Chained scenarios with no single playbook entry, where fixing one fault reveals the next. The agent has to work the chain by observation; a flat table of type-to-command has nowhere to look up "what is broken now."
8. **Transcript-tell detection.** Flag submissions that remediate without first observing state: near-zero inspection before acting, constant latency, identical command shapes. This is an audit signal for the leaderboard, not a hard gate, but it surfaces the playbook pattern directly.

Proactive-detection mode (the agent must notice the problem from signals, not be told the fix) is inherently the hardest format to game, which is why Wave 1 biases the mix toward it (~50%, with no-op and trap scenarios living inside that share).

### Private hold-out: needs discussion with Google, with a known limitation

A private hold-out of whole task _families_ (not just instances) is the only thing that fully defeats pre-solving the known type set. It is also not airtight, so we frame it honestly rather than as a clean win.

- **Known limitation.** A determined entrant can erode the hold-out by repeated submissions. They probe it: submit variants, observe pass/fail, and reconstruct the tasks and solutions over many runs. A hold-out raises the cost of the attack; it does not eliminate it.
- **Levers that slow probing** (all to be worked out with Google, none a silver bullet): return aggregate scores only, not per-task pass/fail; meter or rate-limit submissions per entrant; run a sealed one-shot official evaluation (submit the agent, it runs once on the current private set, no iterating); rotate the scored pool faster than it can be mapped, with sparse per-run sampling from a large pool; and detect probing behavior.
- **Honest conclusion.** Secrecy is a secondary layer. The durable defense is in-task run-time diagnosis (root-cause randomization and the proactive/diagnosis-heavy set), which makes even a fully-known task family still require real competence to solve.

---

## Execution plan: the 6-8 week sprint and the later-wave roadmap

### Part A: Wave 1 (6-8 weeks, ~115 logical tasks)

The shape of Wave 1 is foundation first, then mass production through the authoring factory. We front-load the deterministic scoring foundation into weeks 1-2 because everything downstream depends on it, and because parametric generation and out-of-band scoring are built in. We then run the factory across the Kubernetes plane (cheapest, on `kind`), the focused GCP Cloud plane (ephemeral sandboxes), and the seam.

| Week | Focus | Owner(s) | Output |
| --- | --- | --- | --- |
| 1-2 | Foundation | Eng1 (verifiers + parametric generation + out-of-band scoring + harness + CI), Eric (taxonomy, templates, quality bar), Eng2 (cloud TF stacks begin), agents (factory prototype) | Resource-existence + config verifiers registered in `spec.py`; parametric task generation (generator + parameterized verifier); out-of-band scoring (agent never sees oracle/verifier); oracle-PASS/baseline-FAIL validation harness; CI; locked taxonomy and category templates; factory proven on 5-10 `kind` generators |
| 2-4 | Kubernetes plane bulk | Eng1 (structured-claim verifier, metric-seeding), agents (authoring), Eric (review gate) | ~68 k8s tasks via the factory on `kind`; diagnosis-report unlocked; proactive-detection metric seeding live |
| 4-6 | Focused GCP cloud slice + start the seam | Eng2 (lead, cloud-resource verifiers, one TF stack pattern per category), agents (authoring), Eric (review gate) | ~30 Cloud-plane tasks across the focused 7-category slice; `gcloud`/cloud-API existence and config checks; seam authoring begins |
| 6-7 | Seam + harden + quality sweep | Eng2 (seam on GKE), Eng1/Eric (quality sweep), agents (authoring) | ~17 seam tasks on GKE; quality sweep across the catalog |
| 7-8 | 3 P0 docs + Google pitch + buffer | Eric (Google brief + pitch polish), Eng1/Eng2 (final gate pass), agents (docs) | PM/Google brief; quickstart; reference tutorial agent; final oracle/baseline gate pass; schedule buffer; Google pitch polished |

Note: shared boundary weeks (e.g., week 2 appears in both "1-2" and "2-4") are handoff weeks, not double-counted time.

**Critical path.** The chain is scoring foundation (weeks 1-2) then factory then all authoring. Nothing gets authored at volume until the resource-existence and config verifiers, parametric generation, out-of-band scoring, the validation harness, and CI exist, because the factory's quality gate (apply oracle, all checks PASS; apply baseline, all checks FAIL, across sampled parameterizations) runs on top of them. The foundation now includes parametric generation and out-of-band scoring, which is why it is a two-week phase and why the wave is right-sized at ~115. The single biggest risk to the timeline is the foundation slipping, so it is staffed first and kept deliberately lightweight: we extend the existing verifier framework and reuse the `gcli`/`openclaw` execution path rather than building the black-box runner.

**Dependency note.** The structured-claim verifier gates diagnosis-report mode, so that mode stays capped until the verifier lands in Weeks 2-4. The Cloud plane and seam depend on Eng2's terraform stacks, which start in the foundation phase and run ahead of the authoring waves that consume them.

### Definition of done / quality bar (per task)

A task is not landed until all of the following hold:

- **Oracle PASSes.** Applying the correct end-state makes every check pass, across sampled parameterizations.
- **Baseline FAILs.** Applying only the seeded baseline makes the checks fail, across sampled parameterizations.
- **Deterministic given parameters.** The same end-state yields the same result every run for a given parameterization.
- **Realistic and un-cheeseable.** The scenario is plausible and the check cannot be passed trivially or by accident.
- **Clean lifecycle.** Provisioning and teardown are clean, with no leaked resources.

### Wave 1 exit criteria

- ~115 logical tasks landed (68 Kubernetes, 30 Cloud, 17 seam; multicloud deferred), each through the oracle/baseline gate.
- The four committed integrity properties (parametric generation, out-of-band scoring, root-cause randomization, and the proactive/diagnosis-heavy set with no-op and trap tasks) live for all landed tasks.
- Mode mix roughly proactive-detection 50%, instructed 30%, diagnosis-report 20% (no-op and trap scenarios within the proactive-detection share, diagnosis-report still contingent on the structured-claim verifier landing); difficulty roughly simple 60%, complex 40%.
- Cloud-facing content is roughly 40% of the catalog, up from a rounding error today.
- The three P0 docs shipped: PM/Google brief, quickstart, reference tutorial agent.
- CI green; deterministic foundation in `spec.py`; no LLM-as-judge in the scoring path for landed tasks.

### Part B: Later-wave roadmap

The unlock for later waves is the deployment-target abstraction: pull the `gcloud` credential fetch out of `TFDeployer`, add a `CredentialsFetcher` per cloud, expand `PROVIDER_RESOLVERS` beyond `{gcp, kind}`, and add a `target:` field to `task.yaml`. `TFDeployer`'s apply/destroy loop is already cloud-agnostic, so this is a contained abstraction, not a rewrite. Once it lands, parity ports are largely an authoring problem the factory already solves.

| Wave | Focus | Rough adds | Running total |
| --- | --- | --- | --- |
| 1 | Two-plane GCP-first catalog (k8s + focused cloud slice + seam) | ~115 | ~115 |
| 1b | Deferred Cloud-plane categories (C5 VM compute, C7 FinOps, C8 cloud observability, C9 messaging, C12 DNS/edge/CDN), the integrity fast-follows (behavioral checks and blast-radius invariants are discrete verifier-shaped controls promoted to core once the foundation is stable; multi-fault composition is woven in as task families mature, not promoted as a discrete verifier; transcript-tell detection lands alongside the private-hold-out/leaderboard policy work from the Google discussion, not as a Wave-1 verifier), and the thin multicloud slice pulled from Wave 1 (cross-cluster failover, cross-cloud DNS failover, multi-cluster traffic/mesh split, cross-cloud backup/restore, cross-cloud identity federation), biased to deterministic control-plane assertions | ~40 | ~155 |
| 2 | Deployment-target abstraction, then AWS/EKS parity for ~45 portable tasks + AWS-unique (IRSA/OIDC, VPC-CNI IP exhaustion, GuardDuty EKS runtime, `aws-auth` to Access Entries) | ~50 | ~205 |
| 3 | Azure/AKS parity for the same ~45 + Azure-unique (Entra Workload Identity, resource-lock blocking destroy, Azure Arc multi-cluster GitOps, Defender for Containers) | ~50 | ~255 |
| 4 | Deeper Cloud-plane breadth and true multicloud expansion as the abstraction matures | ~15-45 | ~270-300 |

The end state is roughly 270-300 concrete cases spanning both planes across GCP, AWS, and Azure, with GCP-first depth and credible parity on the other two. The factory built in Wave 1 is what makes the later waves cheap: parity is mostly re-targeting and re-authoring against templates the team already owns, not new infrastructure.

---

## Risks, dependencies, open decisions, and docs

### Risk register

We track seven risks for Wave 1. Likelihood and impact are qualitative (Low / Medium / High).

| # | Risk | Likelihood / Impact | Mitigation |
|---|------|---------------------|------------|
| R1 | **Greenfield velocity.** Going from 14 tasks to 115 in 6 to 8 weeks depends on the authoring factory and the quality gate holding. | Medium / High | Front-load the foundation into weeks 1-2, then run the factory at ~15 to 20 landed tasks/week. The smaller scope (115 rather than 150) plus the full 8-week runway materially de-risk it. Start with k8s/kind tasks (free, fast loop) to prove the loop before paying for cloud resources. Treat the factory loop itself as a foundation-phase deliverable, not an assumption. |
| R2 | **Google foundation timing / contract.** A Google-provided scoring foundation could arrive late or land with a different contract than ours. | Medium / Medium | Build thin and own it ourselves: extend the existing verifier framework (`pkg/agents/verifier/spec.py`), reuse the `gcli`/`openclaw` execution path, and match the eventual contract loosely so a Google foundation could swap in. Do not block any authoring on Google. |
| R3 | **Cloud spend + non-determinism.** Cloud-plane verification consumes real GCP resources and risks flaky, non-deterministic checks. | Medium / High | Keep the entire k8s plane (~68) and the seam loop on kind for free. Restrict spend to the focused Cloud plane (~30) and the GKE seam (~17), with one terraform stack pattern per category and tight, enforced teardown. Bias checks to deterministic resource existence and configuration facts, not timing-sensitive state. |
| R4 | **Diagnosis mode capped.** `diagnosis-report` tasks cannot be scored deterministically until the structured-claim verifier lands. | Medium / Medium | Cap `diagnosis-report` at ~20% of Wave 1 and sequence the structured-claim verifier into Weeks 2-4. If it slips, convert affected cases to detect-and-fix (see Decision 3). |
| R5 | **No black-box runner: future BYO-agent tradeoff.** Skipping the black-box runner keeps execution coupled to `gcli`/`openclaw`. Fine today, but a constraint if third-party bring-your-own-agent submissions become a goal. | Low / Medium | Accept the coupling for Wave 1. Keep the verifier contract clean and runner-agnostic so the execution layer can be decoupled later without touching task content. Revisit only if external submissions become a real requirement. |
| R6 | **Quality-bar erosion under pressure.** Timeline pressure tempts us to land tasks that are cheeseable or non-deterministic. | Medium / High | Enforce the automated gate on every task across sampled parameterizations: oracle end-state must PASS all checks, seeded baseline must FAIL. Add a human spot-check for realism and no-cheese before a task counts toward the wave. Gaming risk is addressed in-design (parametric generation + out-of-band scoring) rather than left open. The gate is non-negotiable; a task that does not pass it does not land. |
| R7 | **Parametric generation adds foundation complexity.** Building a generator plus a parameterized verifier per task family is more work than a static fixture. | Medium / Medium | Start with a small set of parameter axes per task family and widen later. It is the reason the foundation is a two-week, first-staffed phase. The payoff is a benchmark that is hard to memorize and hard to cheese, so it is worth the up-front cost. |

### Open decisions we still need from you

These are the calls we need from Eric to close out the plan. The rest of the plan does not block on them, but later-wave scope and the diagnosis-mode share do.

1. **Cloud-parity scope.** For later waves, do we target full parity (~45 portable tasks ported to each of AWS and Azure) or a curated proof subset that demonstrates the abstraction without the full porting cost?
2. **Integrity fast-follows: forward path for all four.** Behavioral checks and blast-radius invariants are discrete verifier-shaped controls: when do we promote them to core? Multi-fault composition is an authoring pattern, not a discrete verifier: when are task families mature enough to weave it in? Transcript-tell detection is a leaderboard-time audit signal that lands alongside the private-hold-out/leaderboard policy work (Decision 5), not a Wave-1 verifier. Separately: how many parameter axes do we randomize per task family in Wave 1?
3. **Commit to the structured-claim verifier, or shrink diagnosis mode.** Do we commit to building the structured-claim verifier (keeping `diagnosis-report` alive at ~20%), or convert most diagnosis cases to detect-and-fix and drop the verifier from the critical path?
4. **The Google pitch headline.** What is the one-line framing we lead with? Current candidate: the neutral, two-plane standard for evaluating DevOps agents, scored on resource facts rather than LLM-as-judge, and parametric and out-of-band so it is hard to game or contaminate.
5. **Private hold-out strategy with Google.** Whether and how to run a private hold-out of whole task families given that repeated submissions can erode it. Levers to settle: aggregate-only scoring, submission metering, sealed one-shot evaluation, pool rotation, and probing detection.

### Docs plan

Three P0 docs land in Weeks 7-8, alongside the quality sweep.

| Doc | Audience | Purpose |
|-----|----------|---------|
| PM / Google brief | Google leadership, PM | The buy-in pitch: the two-plane standard, deterministic outcome scoring, parametric and out-of-band integrity, GCP-first with phased AWS/Azure parity, and what the investment buys (a defensible benchmark, broad cloud coverage, a low-headcount authoring factory). |
| Quickstart | New contributors and internal engineers | Get from clone to a passing local run on kind: prerequisites, env vars (`PROJECT_ID`, `CLUSTER_NAME`), how to run the evaluate flow, and how the oracle/baseline gate works. |
| Reference tutorial agent | Adopters evaluating their own agents | A worked, end-to-end example agent run against a known task, showing the execution path and how scoring is produced, so external teams can wire in their own agent. |
