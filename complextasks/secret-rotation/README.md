## Setup

### 1. Grant GCP IAM Permissions to Agent VM
For the agent to successfully rotate secrets via GCP Secret Manager, the agent's runner VM service account (e.g., `openclaw-vm-sa`) must have Secret Manager Admin permissions:

```bash
# Set your target project ID
export GCP_PROJECT_ID="your-gcp-project-id"
export AGENT_SERVICE_ACCOUNT="openclaw-vm-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${AGENT_SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.admin" \
    --condition=None
```

### 2. Prepare Cluster Environment
Run the automated setup script to deploy all GKE manifests and initialize Secret Manager:

```bash
GCP_PROJECT_ID="${GCP_PROJECT_ID}" \
GKE_CLUSTER_NAME="${GKE_CLUSTER_NAME}" \
GCP_LOCATION="${GCP_LOCATION}" \
NAMESPACE="${NAMESPACE}" \
./complextasks/secret-rotation/setup/setup.sh
```

## Evaluation

Export the required env vars and run the eval:

```bash
.venv/bin/python3 pkg/evaluator/evaluate.py complextasks/secret-rotation/task.yaml
```

