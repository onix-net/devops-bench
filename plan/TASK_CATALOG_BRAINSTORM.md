# devops-bench work catalog: the full backlog (v3)

Status: this is the full multi-wave backlog and idea space, organized to match [`PROJECT_AND_STAFFING_PLAN.md`](./PROJECT_AND_STAFFING_PLAN.md). The plan is the committed Wave 1 (~115 tasks). This catalog is the superset across all waves: the full taxonomy and the broader backlog the authoring factory draws from. Nothing here outside the Wave 1 columns is committed; treat it as an idea space to argue with.

The two documents are designed not to contradict each other. Where they overlap (Wave 1 counts, integrity controls, the deployment-target abstraction), the plan is the source of truth and this catalog restates it. Where this catalog goes further (later-wave categories, AWS/Azure parity, the cross-cloud seam matrix, multicloud), it is backlog the plan deliberately defers.

## Relationship to the plan

| Document | Scope | What it owns |
| --- | --- | --- |
| `PROJECT_AND_STAFFING_PLAN.md` | Committed Wave 1 (~115) | Execution plan, staffing/RACI, velocity, the authoring factory, benchmark integrity, definition of done, the wave roadmap |
| This catalog (v3) | Full backlog, all waves | The complete two-plane taxonomy, per-category example tasks, the seam matrix, AWS/Azure parity, multicloud, and the platform/harness capability list the factory builds against |

Read the plan for "what we are shipping and how." Read this catalog for "the whole space the factory can pull from."

---

## The axes

Every task in the catalog is located on three axes. This is the same spine as the plan.

1. **Plane.** Where the system under test lives.
   - **Plane 1, Kubernetes**: cloud-agnostic, runs on `kind`. The cluster is the system under test. The free, fast backbone.
   - **Plane 2, Cloud platform**: no cluster required. The cloud control plane is the system under test. GCP-first in Wave 1, with AWS/Azure analogs in later waves.
   - **The seam (cloud-specific-in-k8s)**: Kubernetes tasks whose difficulty comes from the cloud underneath (Workload Identity, cloud LoadBalancers, cloud StorageClasses). GCP-first in Wave 1; the GKE/EKS/AKS matrix is a later wave.
   - **Multicloud**: spans two or more clouds or clusters at once. Deferred out of Wave 1.
2. **Interaction mode.** `instructed` (the prompt names the action), `proactive-detection` (the agent must notice the problem from signals), `diagnosis-report` (the agent emits a structured root-cause claim). Biased toward proactive-detection because it is the hardest format to game.
3. **Difficulty.** `simple` or `complex`, a lighter fourth axis.

Wave 1 mode mix (from the plan): proactive-detection ~50%, instructed ~30%, diagnosis-report ~20% (diagnosis capped until the structured-claim verifier lands). Difficulty roughly simple 60%, complex 40%.

Tags below read `[plane · mode · difficulty]`. We use the plane name (`k8s`, `gcp`, `seam`, `matrix`, `multicloud`) where the older tier language used to sit.

---

# Stream A: the benchmark catalog (two planes)

This is the content an agent is scored against, organized by plane. The Wave 1 columns are the plan's committed numbers and must match it exactly. The full-target columns are the eventual GCP-first depth, approximate and uncommitted.

## Plane 1: Kubernetes

Cloud-agnostic, runs on `kind`, so the authoring loop is free and fast. This is why the k8s plane goes first in the factory. Wave 1 sums to 68 (the plan's allocation).

| Category | Wave 1 | Full target | Notes |
| --- | ---: | ---: | --- |
| 1. Rollout, progressive delivery & rollback | 6 | 9 | Canary/blue-green, SLO gates, rollback safety. Fully k8s-portable. |
| 2. Scheduling, bin-packing & right-sizing | 6 | 9 | Requests/limits, topology spread, eviction pressure. Fully k8s-portable. |
| 3. Autoscaling (HPA/KEDA/cluster-autoscaler), k8s portion | 4 | 6 | The in-cluster slice; node-side and cloud-event-source autoscaling sit in Plane 2 / parity. |
| 4. Workload crash & pod lifecycle remediation | 7 | 10 | OOMKills, probes, crash loops. The richest k8s-native vein. |
| 5. Storage, volumes & disk-pressure, k8s portion | 4 | 8 | PVC binding, disk-pressure eviction, snapshot restore; cloud CSI specifics sit in parity. |
| 6. Stateful recovery & DR, k8s portion | 3 | 9 | In-cluster restore from VolumeSnapshot; cross-cluster/cloud DR moves to multicloud. |
| 7. Cluster networking (DNS/Services/LB), k8s portion | 4 | 8 | CoreDNS, Services, kube-proxy; cloud LB/DNS specifics sit in the seam and Plane 2. |
| 8. NetworkPolicy, RBAC & admission guardrails | 5 | 9 | Default-deny, broken webhooks, RBAC lockouts. Mostly k8s-portable; CNI enforcement is a seam concern. |
| 9. Secrets, TLS & cert lifecycle, k8s portion | 4 | 9 | In-cluster Secret/TLS rotation, cert-manager; cloud secret stores sit in the seam and Plane 2. |
| 10. Supply chain (provenance/signing/CVE), k8s portion | 3 | 7 | Image CVE detection, admission policy; cloud registries/attestation sit in parity. |
| 11. GitOps & IaC drift, k8s portion | 4 | 9 | Reconcile out-of-band mutations; cloud IaC backends sit in Plane 2 (C11). |
| 13. Spot resilience & chaos, k8s portion | 4 | 8 | PDBs, graceful drain, disruption budgets; cloud spot-eviction timing sits in the seam. |
| 14. Observability & SLOs, in-cluster portion | 4 | 10 | Burn-rate alerts, in-cluster metrics; cloud monitoring/billing sit in Plane 2 (C8). |
| 15. GPU & AI inference platform ops, k8s portion | 3 | 9 | Device plugins, scheduling, inference fallback; cloud GPU pools sit in the seam/parity. |
| 16. Database & stateful-data, in-cluster portion | 2 | 7 | In-cluster DB ops (pool exhaustion, StatefulSet); managed DBs sit in Plane 2 (C2). |
| 17. Service mesh & L7 traffic management | 5 | 6 | mTLS, sidecar injection, traffic shifting. Mostly portable; managed-mesh differs per cloud. |
| **Sum, Plane 1** | **68** | | |

### Per-category example tasks (Plane 1)

Two strong titles per category, preserved from the brainstorm and tagged `[plane · mode · difficulty]`. Categories that span planes (3, 5, 6, 7, 9, 10, 11, 13, 14, 15, 16) keep cloud-flavored example titles where they best illustrate the category; those specific titles belong to the seam or Plane 2 in the new structure, but they stay here as the canonical examples for the category's intent.

1. **Rollout**: Abort a canary spiking 5xx before saturation `[k8s · proactive-detection · complex]`; Promote only after SLO gates pass `[k8s · instructed · simple]`
2. **Scheduling**: Stop eviction pressure from 10x-over-provisioned memory requests `[k8s · proactive-detection · complex]`; Spread a StatefulSet across three zones `[k8s · instructed · simple]`
3. **Autoscaling**: Fix a Pub/Sub KEDA HPA that never scales out (missing WI role) `[gcp · proactive-detection · complex]`; Diagnose why cluster autoscaler won't add a node `[gcp · diagnosis-report · complex]`
4. **Workload crash**: Stabilize OOMKilled workers with no memory ceiling `[k8s · proactive-detection · simple]`; Fix a liveness probe killing a slow-starting JVM `[k8s · proactive-detection · simple]`
5. **Storage**: Stop a Postgres eviction loop from WAL disk exhaustion `[k8s · proactive-detection · complex]`; Expand a regional PD PVC without downtime `[gcp · instructed · simple]`
6. **Stateful/DR**: Restore Postgres from a VolumeSnapshot after data loss `[k8s · instructed · complex]`; Promote a Postgres read-replica to primary after losing the primary `[k8s · proactive-detection · complex]`
7. **Networking**: A CoreDNS rewrite silently breaks internal lookups `[k8s · proactive-detection · simple]`; Diagnose Cloud NAT SNAT-port exhaustion `[gcp · diagnosis-report · complex]`
8. **NetPol/RBAC/admission**: A default-deny policy locks out kubelet probes `[k8s · proactive-detection · simple]`; Recover a cluster where a broken webhook blocks all Pod creation `[k8s · proactive-detection · complex]`
9. **Secrets/TLS**: Zero-downtime rotation of a Secret Manager secret via ExternalSecrets `[gcp · instructed · complex]`; GKE managed cert stuck PROVISIONING on a wrong DNS record `[gcp · proactive-detection · complex]`
10. **Supply chain**: Detect a workload on a critical-CVE image and remediate `[k8s · proactive-detection · complex]`; Diagnose why Binary Authorization is blocking a rollout `[gcp · diagnosis-report · complex]`
11. **GitOps/IaC drift**: Reconcile an out-of-band replica-count mutation `[k8s · proactive-detection · simple]`; A firewall rule widened to 0.0.0.0/0 during an incident `[gcp · proactive-detection · simple]`
12. **CI/CD & upgrades**: Fix a Cloud Build trigger broken by a revoked SA role `[gcp · proactive-detection · simple]`; Surge-upgrade a node pool with strict PDBs `[gcp · instructed · complex]`
13. **Spot/chaos**: Remediate a spot-pool drain causing Pending prod pods `[gcp · proactive-detection · complex]`; Add a PDB so an API survives a rolling spot interruption `[k8s · instructed · simple]`
14. **Observability/cost**: Detect a silently-misfiring burn-rate alert `[k8s · proactive-detection · complex]`; Decommission idle LoadBalancer Services bleeding egress cost `[k8s · proactive-detection · simple]`
15. **GPU/AI**: Fix a vLLM deployment silently falling back to CPU `[k8s · proactive-detection · simple]`; Cordon a node with persistent GPU Xid errors `[gcp · proactive-detection · simple]`
16. **Database**: Connection-pool exhaustion: replicas x pool > max_connections `[k8s · proactive-detection · complex]`; Cloud SQL private-IP broken after a VPC peering change `[gcp · proactive-detection · complex]`
17. **Service mesh**: STRICT mTLS breaks a legacy plaintext client `[k8s · proactive-detection · complex]`; Sidecar not injected because the namespace label is missing `[k8s · proactive-detection · simple]`

Note: the old Category 12 (CI/CD & cluster-upgrade operations) and Category 18 (cloud control-plane: quota/IAM/API enablement/org-policy) are GCP control-plane work in intent. In the two-plane model their substance lives in Plane 2 (C4 identity/governance, C11 IaC, plus upgrade/CI scenarios). Their example titles are retained above so no detail is lost.

## Plane 2: Cloud platform (C1-C12)

No cluster required. The cloud control plane is the system under test. GCP-first in Wave 1, deliberately deep on a focused 7-category slice rather than thin across all twelve. These tasks cost real cloud resources to validate, so they run against ephemeral sandboxes with tight teardown.

Wave 1 column is exact (the plan's allocation, sum 30). Full-target column is approximate eventual GCP-first depth.

| ID | Category | Wave 1 | Full target | Example tasks |
| --- | --- | ---: | ---: | --- |
| C4 | Identity, IAM & org governance (service accounts/roles/WIF/Org Policy/KMS) | 6 | 8 | GitHub Actions OIDC to GCP via Workload Identity Federation is failing; an Org Policy constraint blocks a legitimate deploy; rotate a KMS key without breaking decryption |
| C3 | Cloud networking (VPC/subnets/routes/peering/Cloud NAT/PSC/firewall, non-k8s LB) | 5 | 7 | Two VPCs cannot talk after peering due to overlapping CIDR or a missing route; a Private Service Connect endpoint cannot resolve |
| C2 | Managed data services (Cloud SQL/Spanner/BigQuery/Memorystore) | 5 | 7 | Point-in-time-restore a Cloud SQL instance after bad data; fix a read-replica lag that is blowing the RPO; a BigQuery scheduled query silently fails on a permissions change |
| C1 | Serverless & app platforms (Cloud Run/Functions/App Engine) | 4 | 6 | Cloud Run service 403s because the invoker IAM binding is missing; a Function times out on a VPC-connector cold start |
| C10 | Cloud security posture (SCC/CSPM/public exposure/encryption-at-rest) | 4 | 6 | Remediate a public-exposure finding without an outage; enforce CMEK on a non-compliant resource |
| C6 | Object/block storage & data lifecycle (GCS buckets/lifecycle/versioning/retention/public-access) | 3 | 5 | A bucket is world-readable, lock it down without breaking the app; a lifecycle rule is deleting data it should not |
| C11 | Cloud IaC & provisioning safety (OpenTofu plan/drift/import/destructive-change guard) | 3 | 5 | A `tofu plan` shows a destructive replacement, explain why and make it non-destructive; import an out-of-band-created resource into state |
| C5 | VM compute & instance groups (Compute Engine/MIGs/autohealing/templates) | 0 | 5 | A managed instance group is not autohealing because the health check is misconfigured; a rolling instance-template update is stuck; right-size an over-provisioned MIG |
| C7 | FinOps & budgets (budgets/alerts/committed-use/cost anomalies) | 0 | 5 | A monthly budget has no alert wired so spend overran silently; detect a cost anomaly from a forgotten high-tier resource; a committed-use discount is not being applied |
| C8 | Cloud observability (Cloud Monitoring/Logging/log-based alerts/uptime checks) | 0 | 5 | A log-based metric alert never fires because the filter is wrong; an uptime check is green but the service is down (wrong target); dashboards lost a metric after a label change |
| C9 | Messaging & async (Pub/Sub/Tasks/Eventarc) | 0 | 5 | A Pub/Sub subscription backlog is growing because the dead-letter policy and ack deadline are misconfigured; an Eventarc trigger silently drops events on a missing IAM role |
| C12 | DNS, CDN & edge (Cloud DNS/Cloud CDN/load-balancer edge) | 0 | 5 | A Cloud DNS record points at a decommissioned IP; Cloud CDN is serving stale content because cache invalidation/TTL is wrong; an edge LB returns 502 on a bad backend health check |
| | **Sum, Plane 2 (Wave 1)** | **30** | | |

The deferred categories (C5, C7, C8, C9, C12, all 0 in Wave 1) move to Wave 1b. Wave 1 goes deep on the focused slice rather than thin across all twelve.

## The seam: cloud-specific-in-k8s

Kubernetes tasks whose difficulty comes from the cloud underneath. GCP-first in Wave 1 (17 tasks, the plan's allocation). The cross-cloud GKE/EKS/AKS matrix expansion is a later wave.

### Wave 1 seam (GCP-first, 17)

Representative cases, from the plan:

- Workload Identity for a pod to read a cloud secret with no mounted credential.
- Internal LoadBalancer with a static IP via the right annotation dialect.
- Default StorageClass / PVC binding on a fresh cluster.
- A CoreDNS stub zone that survives an upgrade.
- A NetworkPolicy that is actually enforced by the CNI, not just applied.
- A GPU/spot node pool with a tolerating workload.
- API-server audit logging to find who deleted a Deployment.

These seven patterns plus their parametric variants fill the 17-task Wave 1 seam.

### Later-wave seam matrix expansion (cross-cloud GKE/EKS/AKS quirks)

The same goal, three cloud-specific fixes. These exist because GKE, EKS, and AKS differ in ways that change how a task behaves and how it is scored. Each is one logical case implemented as a GKE/EKS/AKS matrix; the outcome check is cloud-agnostic (the resource ends up correct) but the path differs per cloud. This is the later-wave expansion of the seam, gated on the deployment-target abstraction. Strong candidates (preserved from the brainstorm's Category 19):

- **Internal LoadBalancer with a static IP**: same Service, three annotation dialects (`cloud.google.com/load-balancer-type: Internal` vs `service.beta.kubernetes.io/aws-load-balancer-internal` vs `azure-load-balancer-internal` + pre-allocated PIP). Wrong annotations silently create the wrong LB. `[matrix · instructed · simple]`
- **Pod reads a cloud secret with native workload identity, no mounted credential**: Workload Identity (KSA annotation) vs IRSA (OIDC trust policy) vs Entra Workload Identity (federated credential). `[matrix · instructed · complex]`
- **Fresh-cluster PVC binding for a ReadWriteOnce StatefulSet**: GKE ships a default StorageClass; EKS often has none until the EBS CSI add-on is enabled; AKS uses `managed-csi`. `[matrix · proactive-detection · simple]`
- **Add a custom CoreDNS stub zone that survives upgrades**: the authoritative ConfigMap differs (`coredns-user` vs `coredns` add-on schema vs `coredns-custom`); editing the wrong one gets silently reverted. `[matrix · proactive-detection · complex]`
- **Enforce a default-deny NetworkPolicy that is actually enforced**: enforcement depends on the CNI (GKE Dataplane V2 vs EKS needing a policy controller vs AKS `azure`/`calico` chosen at creation). The agent must verify enforcement, not just that the object applied. `[matrix · proactive-detection · complex]`
- **Add a GPU/spot node group and schedule a tolerating workload**: node pools vs managed node groups/Karpenter vs VMSS node pools. `[matrix · instructed · complex]`
- **Spot eviction handling**: 25s (GKE) vs 2min + required NTH DaemonSet (EKS) vs 30s Scheduled Events (AKS). `[matrix · proactive-detection · complex]`
- **Enable API-server audit logging and find who deleted a Deployment**: on by default (GKE) vs off until enabled (EKS per-type, AKS diagnostic settings). `[matrix · diagnosis-report · complex]`
- **Fix a StatefulSet stuck Pending on a volume-zone affinity conflict**: `WaitForFirstConsumer` binding (EKS footgun) vs ZRS StorageClass for AZ survival (AKS). `[matrix · proactive-detection · complex]`
- **Complete a cluster upgrade blocked by a managed add-on conflict / deprecated add-on**: release channels (GKE) vs add-on conflict-resolution mode (EKS) vs deprecated-addon block (AKS). `[matrix · proactive-detection · complex]`

Counting: each quirk is one logical case implemented as a GKE/EKS/AKS matrix, so ~10 logical maps to ~30 concrete. Whether to count the matrix as logical or concrete is an open question (below).

## Multicloud

Spans two or more clouds or clusters at once. Deferred out of Wave 1 because it is the most expensive to provision and the least deterministic. The thin multicloud slice lands in Wave 1b, biased to deterministic control-plane assertions. Representative later-wave scenarios:

- Cross-cluster primary/replica failover under traffic (for example, Redis or Postgres).
- Cross-cloud DNS failover (health-checked record flip between providers).
- Multi-cluster traffic / mesh split across clouds.
- Cross-cloud backup and restore (snapshot in one cloud, restore in another).
- Cross-cloud identity federation (a workload in one cloud assuming a role in another).

## Cloud parity (AWS & Azure expansion)

This is the **Wave 2-3** expansion, not Wave 1. Most genuinely cloud-specific Plane 2 and seam tasks have an AWS and Azure analog that solves the same problem with different products. The benchmark value is real because the wiring differs even when the goal is identical. The k8s-portable categories (1, 2, 4) port with little change.

| Category | GCP | AWS | Azure | Parity |
| --- | --- | --- | --- | --- |
| Autoscaling (node side) | GKE node pools / NAP, Pub/Sub KEDA | Karpenter / MNG, SQS KEDA | VMSS node pools, Service Bus KEDA | clean |
| Storage CSI | PD / Filestore / Parallelstore | EBS / EFS / FSx-Lustre | Azure Disk / Files / NetApp Files | clean (AWS), partial (Azure) |
| DR & backup | Velero+GCS, Cloud SQL HA, Cloud DNS | Velero+S3, RDS Multi-AZ, Route 53 | Velero+Blob, Flexible Server geo, Front Door | clean / partial |
| LB & DNS | GCLB, NEG, Cloud DNS | ALB/NLB via LBC, Route 53 | Azure LB / App Gateway (AGIC), Azure DNS | partial (annotation-divergent) |
| IAM ↔ RBAC | Workload Identity, IAM roles, Org Policy | IRSA / Pod Identity, aws-auth / Access Entries, SCPs | Entra Workload Identity, Azure RBAC, Azure Policy | partial |
| Secrets & TLS | Secret Manager + ESO, Managed Certs | Secrets Manager + ESO/ASCP, ACM | Key Vault + CSI, cert-manager (azuredns) | clean |
| Supply chain | Artifact Registry, Binary Auth, Cosign | ECR + Inspector, Signer/Notation, Kyverno | ACR, Defender, Notation/Ratify | clean / partial |
| IaC backend | tofu + GCS | tofu + S3 + DynamoDB lock | tofu / Bicep, Azure Arc Flux | clean |
| Upgrades & CI | GKE release channels, Cloud Build | EKS manual + eksctl, CodeBuild | `az aks upgrade` + maint windows, Azure Pipelines | partial |
| Spot | GKE Spot (25s SIGTERM) | EC2 Spot (2min) + NTH + Karpenter, FIS | Azure Spot (30s) + Scheduled Events, Chaos Studio | clean (AWS needs an NTH DaemonSet) |
| Observability & cost | GMP + Cloud Monitoring, Billing/BQ | AMP + Grafana, CloudWatch, Cost Explorer / Kubecost | Azure Monitor / Managed Prom, Cost Management | clean / partial |
| GPU & inference | A100/H100, Parallelstore | P4d/P5 + Neuron, FSx-Lustre | NC/ND + InfiniBand, NetApp Files | partial (AWS adds Neuron; Azure adds InfiniBand) |
| Database | Cloud SQL, Auth Proxy | RDS / Aurora, RDS Proxy | Flexible Server, Private Endpoint | clean |
| Service mesh | Anthos SM / Traffic Director, Istio | App Mesh / VPC Lattice, Istio | AKS managed Istio add-on, AGC | partial (managed mesh differs; Istio portable) |
| Cloud control-plane | API enablement, quota, Org Policy | Service Quotas, SCPs, Config (no API-enable concept) | Resource Provider registration, Azure Policy, Quotas | partial |

**Cloud-unique tasks** (no clean GCP analog, worth building for coverage in Wave 2-3):

- **AWS:** IRSA / OIDC trust-policy misconfiguration; EKS VPC CNI IP exhaustion → prefix delegation; GuardDuty EKS Runtime finding containment; aws-auth to Access Entries / Pod Identity migration; Nitro Enclave attestation.
- **Azure:** Entra Workload Identity + Conditional Access / PIM; Azure Resource Lock blocking a `terraform destroy`; Azure Arc multi-cluster GitOps governance (cloud + on-prem); Defender for Containers runtime alert + Logic App remediation.

## How the catalog grows

The wave/growth roadmap, aligned to the plan. Wave 1 is the committed thing; later waves are mostly authoring on top of an abstraction that already works.

| Wave | Content | Rough adds | Running total |
| --- | --- | ---: | ---: |
| **1** | Two-plane GCP-first catalog: Plane 1 k8s (68) + focused GCP Cloud plane (30) + seam (17). Multicloud deferred. | ~115 | ~115 |
| **1b** | Deferred Cloud-plane categories (C5 VM compute, C7 FinOps, C8 cloud observability, C9 messaging, C12 DNS/edge/CDN); the integrity fast-follows (behavioral checks, blast-radius invariants); the thin multicloud slice pulled from Wave 1. | ~40 | ~155 |
| **2** | Deployment-target abstraction, then AWS/EKS parity for the ~45 portable tasks + AWS-unique (IRSA/OIDC, VPC-CNI IP exhaustion, GuardDuty EKS runtime, aws-auth to Access Entries). | ~50 | ~205 |
| **3** | Azure/AKS parity for the same ~45 + Azure-unique (Entra Workload Identity, resource-lock blocking destroy, Azure Arc multi-cluster GitOps, Defender for Containers). | ~50 | ~255 |
| **4** | Deeper Cloud-plane breadth and true multicloud expansion (including the seam matrix across GKE/EKS/AKS) as the abstraction matures. | ~15-45 | ~270-300 |

End state: roughly 270-300 concrete cases spanning both planes across GCP, AWS, and Azure, GCP-first in depth, with credible parity on the other two. The factory built in Wave 1 is what makes the later waves cheap: parity is mostly re-targeting and re-authoring against templates the team already owns.

---

# Stream B: platform & harness capabilities

Engineering work and spikes, not agent-scored tasks. These are what make deterministic scoring real and unlock later waves. Sizes are S/M/L. Order follows dependencies. This list mirrors the plan's platform workstream; the plan is the source of truth for sequencing.

| # | Item | Kind | Size | Why it matters |
| --- | --- | --- | :---: | --- |
| 1 | **Lightweight deterministic scoring foundation** | verifier | M | Extend the existing verifier framework, do **not** build a black-box runner. Add a resource-existence verifier and a resource-configuration verifier (jsonpath selector + comparator: `eq`, `ne`, `gte`, `lte`, `exists`, `contains`, wildcard paths) as `BaseVerifier` subclasses registered in the `SingleVerificationSpec` union in `pkg/agents/verifier/spec.py`, alongside the shipping `PodHealthyVerifier` and `ScalingCompleteVerifier`. Reuse the existing `gcli`/`openclaw` execution path. These two verifiers cover the bulk of Wave 1. Everything else depends on this. |
| 2 | **Parametric task generation** | foundation | M | A task becomes a (generator, parameterized verifier) pair, not a static triplet. The generator randomizes namespaces, names, replica counts, CIDRs, which of N plausible misconfigs is injected, and which resource is broken; the verifier is parameterized to match. The highest-leverage anti-gaming control. Built into the weeks 1-2 foundation. |
| 3 | **Out-of-band scoring** | foundation | S | The agent receives only the prompt and the live environment. `oracle.yaml` and the `verification_spec` are never exposed to the agent. Cheap to enforce; kills the most direct cheese path. Built into the foundation. |
| 4 | **Structured-claim verifier** | verifier | M | Makes diagnosis-report tasks deterministically scorable: the agent emits a structured root-cause/remediation claim (data, not prose) diffed against expected fields. No LLM judge. Unblocks the ~20% diagnosis share. Targeted weeks 2-4. Long-term commit is an open decision. |
| 5 | **In-cluster metric seeding** | harness | L | A deterministic in-cluster signal (a Job/DaemonSet emitting a known Prometheus series or log pattern) so proactive-detection tasks (~50% of Wave 1) have a reproducible thing to notice. Removes the cloud-billing and non-determinism dependency of an LLM-driven load generator. Also underpins behavioral checks. |
| 6 | **Chaos / scenario-injection reuse** | harness | M | Lean on existing stacks under `tf/prebuilt/` (`cp-recovery-kind`, `gpu-stress-test`, etc.) and the existing `chaos_spec` plumbing rather than authoring chaos primitives from scratch. Deterministic kubectl-based faults reachable from the scoring path. |
| 7 | **Deployment-target abstraction** (Wave 2 enabler) | abstraction | L | The enabler for AWS/Azure, explicitly **not** Wave 1 work. Pull the `gcloud` credential fetch out of `TFDeployer` into a per-cloud `CredentialsFetcher`, expand `PROVIDER_RESOLVERS` beyond `{gcp, kind}`, add a `target:` field to `task.yaml`. Detailed below. We design Wave 1 verifiers to be target-agnostic now so this lands cleanly later, but write none of it this wave. |
| 8 | **Blast-radius negative invariants** (designed, not committed) | verifier | M | The "did the agent make it worse" check, promoted to a first-class anti-cheese control but held as a designed-not-committed integrity fast-follow, not Wave 1. Snapshot sibling resources before the run, diff after, fail on unintended changes (broken siblings, widened scope, deletions to satisfy the literal check). The design question is snapshot scope and how to exclude expected controller churn. |

Dependency order: items 1-3 are the weeks 1-2 foundation (the factory's quality gate runs on top of them). Then 4, 5 land in weeks 2-4; 6 reuses existing plumbing alongside. Item 7 (deployment-target abstraction) is the long pole for the multi-cloud story and is Wave 2. Item 8 (blast-radius) is a decision-gated fast-follow.

**Recast / dropped from v2.** The old "outcome-verifier foundation (black-box runner)" item is removed entirely: we are not building `blackbox.py`, `outcome_eval.py`, `resource_exists.py`, `jsonpath_match.py`, or the `adapters/` contract described in `OUTCOME_MVP.md`. The old "BYO-agent contract hardening" / `BLACKBOX_CONTRACT.md` item is recast as a far-later item, revisited only if third-party bring-your-own-agent submissions become a real requirement; it is not on the Wave 1-3 path.

---

# Benchmark integrity

Integrity is a first-class pillar. This is a summary; the plan's [Benchmark integrity](./PROJECT_AND_STAFFING_PLAN.md#benchmark-integrity-making-tasks-hard-to-game) section is the source of truth and should be read for the full threat model and reasoning.

The central principle: the durable defense is **run-time diagnosis**, not secrecy. The strongest gaming vector is a playbook/lookup-table "agent" that maps each task type to a canned command and reads parameters straight from the prompt. Instance randomization and out-of-band scoring do not stop it on their own; only tasks that require diagnosing the specific instance at run time do.

**Committed in Wave 1 (built into the foundation):**

1. **Parametric task generation.** Determinism given per-run parameters that vary. Fresh instance each run, no fixed answer to memorize.
2. **Out-of-band oracle/verifier.** The agent never sees `oracle.yaml` or the `verification_spec`.
3. **Root-cause randomization.** Within a task family, the same observable symptom maps to a randomized underlying cause (Pending pods → quota / taint / oversized request / unbindable PVC / bad `nodeSelector`, chosen per run). A single canned fix is wrong most of the time. The highest-leverage anti-playbook defense.
4. **A proactive- and diagnosis-heavy scored set, with no-op and trap tasks.** The prompt does not name the action. No-op / false-alarm tasks reward reporting healthy or doing nothing; trap tasks make the obvious canned remediation fail or get reverted (a manual scale an HPA reverts, a quota wall that rejects it).

**Designed, not yet committed (decision-gated fast-follow):**

5. **Behavioral checks over config-match** (assert the outcome property, e.g. curl through the LB for a 200, not the mechanism).
6. **Blast-radius negative invariants** (fail if siblings break or scope is widened).
7. **Multi-fault composition** (chained scenarios with no single playbook entry).
8. **Transcript-tell detection** (flag remediation without prior observation; a leaderboard audit signal, not a hard gate).

**Private hold-out: needs a Google discussion, with a known limitation.** A private hold-out of whole task families is the only thing that fully defeats pre-solving the known type set, but it is not airtight: a determined entrant can erode it by repeated submissions (probe, observe pass/fail, reconstruct). Levers to slow probing (aggregate-only scoring, submission metering, sealed one-shot evaluation, pool rotation, probing detection) are all to be worked out with Google, none a silver bullet. Secrecy is a secondary layer; the durable defense remains in-task run-time diagnosis.

---

# The deployment-target abstraction (the Wave 2 enabler)

This is the single change that unlocks the multi-cloud roadmap, and it is grounded in the real code. It is explicitly **not** Wave 1 work. We design Wave 1 verifiers to be target-agnostic so it lands cleanly later, but write none of it this wave.

**Today.** `deployers/factory.py` routes to `TFDeployer` (tofu) or the legacy `GCPDeployer` (kubetest2). `TFDeployer` is cloud-agnostic in its apply/destroy loop, but `get_cluster_info()` hard-codes a `gcloud container clusters get-credentials` call and assumes a GCP project. The factory's `PROVIDER_RESOLVERS` only knows `gcp` and `kind`, and chooses between them by a string heuristic on the stack name. `evaluate.py` requires `PROJECT_ID` / `CLUSTER_NAME` env vars that are GCP-shaped. Every `tf/prebuilt/` stack except `kind` uses the `google` provider.

**What "add a cloud" requires (contained, not a rewrite):**

1. Pull the credential fetch out of `TFDeployer` into a `CredentialsFetcher` per cloud (`gcloud` / `aws eks update-kubeconfig` / `az aks get-credentials`), injected by the factory.
2. Add `deployers/<cloud>/variables.py` implementing `resolve_variables(...)`, mapping harness identity to that cloud's Terraform variables (AWS `region`/account, Azure `resource_group`/`subscription`).
3. Add `tf/prebuilt/<cloud>/...` stacks that emit the two outputs `TFDeployer` reads (`cluster_name`, `cluster_location`).
4. Register the cloud in `PROVIDER_RESOLVERS` and broaden the provider-detection heuristic.
5. Rename the GCP-shaped factory params and placeholder substitution to cloud-neutral names (`global_cluster_id`, `REGION`), filled from `get_cluster_info()` rather than hard-coded env.

**Proposed `task.yaml` change** (makes intent explicit, decouples from the process-level `CLOUD_PROVIDER` env, and is what enables multi-target runs):

```yaml
infrastructure:
  deployer: tofu
  target: aws            # drives the resolver + credentials fetcher
  stack: prebuilt/aws/secret-rotation
  teardown: true
  variables:
    aws_region: us-east-1
    node_count: 2
```

**For true multicloud**, a task declares a list of clusters, each with its own `target`/`stack`, and the evaluator hands the agent a merged kubeconfig with multiple contexts:

```yaml
infrastructure:
  clusters:
    - { target: gcp,   stack: prebuilt/gcp/dr-primary }
    - { target: aws,   stack: prebuilt/aws/dr-standby }
```

**Why a swappable agent doesn't care:** the execution contract (prompt in, act via `$KUBECONFIG`, exit) is already cloud-neutral. The same agent runs against a GKE, EKS, or AKS kubeconfig unchanged. Only control-plane tasks need extra cloud creds, which the harness exports as env vars alongside `KUBECONFIG`. So an agent that handles GCP tasks needs no changes to run on AWS/Azure tasks.

---

# Sequencing

Aligned to the plan's wave plan. Foundation first, then the k8s plane, then the focused GCP cloud slice, then the seam. Multicloud and AWS/Azure later.

1. **Foundation (weeks 1-2).** The lightweight deterministic verifiers (resource-existence + resource-configuration) in `spec.py`, plus parametric task generation and out-of-band scoring built in, plus the oracle-PASS / baseline-FAIL validation harness and CI. Prove the factory on 5-10 `kind` generators. Reuse the `gcli`/`openclaw` execution path; no black-box runner. Everything downstream depends on this.
2. **Kubernetes plane bulk (weeks 2-4).** ~68 tasks via the factory on `kind` (free, fast). Land the structured-claim verifier and metric seeding here; diagnosis-report unlocked.
3. **Focused GCP cloud slice (weeks 4-6).** ~30 Plane 2 tasks across the 7-category slice, with `gcloud`/cloud-API existence and config checks, on ephemeral sandboxes with tight teardown. Start the seam.
4. **Seam (weeks 6-7).** ~17 GCP-first seam tasks on GKE. Harden and run the quality sweep.
5. **Docs + pitch (weeks 7-8).** Three P0 docs (PM/Google brief, quickstart, reference tutorial agent), final gate pass, buffer.
6. **Later waves.** Deployment-target abstraction, then AWS/EKS parity (Wave 2), Azure/AKS parity (Wave 3), then deeper breadth, the seam matrix across clouds, and true multicloud (Wave 4). The thin multicloud slice and the deferred Cloud-plane categories land in Wave 1b.

---

# Open questions

Refreshed against the plan. Resolved items removed: the outcome-MVP / black-box-runner question is settled (we are not building it), and blast-radius is settled as a designed-not-committed integrity fast-follow (not a Wave 1 mandatory). The genuinely open decisions, restated from the plan's open-decisions list:

1. **Cloud-parity scope.** For Wave 2-3, full parity (~45 portable tasks ported to each of AWS and Azure) or a curated proof subset that demonstrates the abstraction without the full porting cost?
2. **Structured-claim verifier commit.** Commit to building it (keeping diagnosis-report alive at ~20%), or convert most diagnosis cases to detect-and-fix and drop the verifier from the critical path?
3. **The Google pitch headline.** The one-line framing we lead with. Current candidate: the neutral, two-plane standard for evaluating DevOps agents, scored on resource facts rather than LLM-as-judge, parametric and out-of-band so it is hard to game or contaminate.
4. **Private hold-out strategy with Google.** Whether and how to run a private hold-out of whole task families given that repeated submissions can erode it. Levers to settle: aggregate-only scoring, submission metering, sealed one-shot evaluation, pool rotation, probing detection.
5. **How many parameter axes to randomize per family in Wave 1.** Start small and widen, but the starting set per task family is an open call. Related: how to count the cross-cloud seam matrix (one logical per quirk, or each cloud variant as its own case so the number reflects the real authoring work).
