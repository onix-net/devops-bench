# Copyright 2026 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the git_repo_sync verifier.

Runs against real, temporary bare git repos under ``tmp_path`` (no ``git``
mocking): more reliable than faking argv/stdout for a subprocess-heavy
verifier. The verifier polls via ``_poll_to_result``; a single immediate
result needs no sleep.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from devops_bench.verification import VerificationSpec
from devops_bench.verification.verifiers.git_repo_sync import GitRepoSyncVerifier

_GIT_CFG = [
    "-c",
    "commit.gpgsign=false",
    "-c",
    "init.defaultBranch=main",
    "-c",
    "safe.bareRepository=all",
    "-c",
    "user.email=devops-bench-test@example.com",
    "-c",
    "user.name=devops-bench-test",
]

_WEB_SEED = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: web
          image: nginx:1.21.6
"""

_WEB_FIXED = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: web
          image: nginx:1.27.4
"""

_APP_SEED = """\
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: web
spec:
  rules: []
---
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: web
spec:
  minAvailable: 1
"""

_APP_FIXED = """\
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
spec:
  rules: []
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web
spec:
  minAvailable: 1
"""


def _run(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *_GIT_CFG, *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout


@dataclass
class GitFixture:
    """A bare repo with a seed commit and a follow-up "fix" commit."""

    bare: str
    seed_sha: str


def _init_repo(tmp_path: Path) -> Path:
    bare = tmp_path / "origin.git"
    work = tmp_path / "work"
    _run(tmp_path, "init", "--bare", str(bare))
    _run(tmp_path, "clone", str(bare), str(work))
    _run(work, "checkout", "-B", "main")
    return work


def _build_git_fixture(tmp_path: Path) -> GitFixture:
    work = _init_repo(tmp_path)
    (work / "workloads").mkdir()
    (work / "workloads" / "web.yaml").write_text(_WEB_SEED)
    (work / "app.yaml").write_text(_APP_SEED)
    _run(work, "add", "-A")
    _run(work, "commit", "-m", "seed")
    seed_sha = _run(work, "rev-parse", "HEAD").strip()
    _run(work, "push", "-u", "origin", "main")

    (work / "workloads" / "web.yaml").write_text(_WEB_FIXED)
    (work / "app.yaml").write_text(_APP_FIXED)
    _run(work, "add", "-A")
    _run(work, "commit", "-m", "fix")
    _run(work, "push")

    return GitFixture(bare=str(work.parent / "origin.git"), seed_sha=seed_sha)


def test_registered_via_spec(tmp_path):
    node = VerificationSpec(
        {"type": "git_repo_sync", "repo_path": str(tmp_path), "op": "exists"}
    ).root
    assert isinstance(node, GitRepoSyncVerifier)


def test_repo_path_tilde_expanded():
    v = GitRepoSyncVerifier.model_validate(
        {"type": "git_repo_sync", "repo_path": "~/nonexistent-xyz.git", "op": "exists"}
    )
    assert not v.repo_path.startswith("~")


def test_image_matches_after_fix(tmp_path):
    fixture = _build_git_fixture(tmp_path)
    v = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "file": "workloads/web.yaml",
            "path": "$[?(@.kind=='Deployment')].spec.template.spec.containers[0].image",
            "op": "matches",
            "value": r"nginx:1\.(2[7-9]|[3-9][0-9])",
        }
    )
    assert v.verify(0).success is True


def test_image_matches_fails_on_seed_ref(tmp_path):
    fixture = _build_git_fixture(tmp_path)
    v = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "ref": fixture.seed_sha,
            "file": "workloads/web.yaml",
            "path": "$[?(@.kind=='Deployment')].spec.template.spec.containers[0].image",
            "op": "matches",
            "value": r"nginx:1\.(2[7-9]|[3-9][0-9])",
        }
    )
    assert v.verify(0).success is False


def test_require_new_commit_true_after_fix(tmp_path):
    fixture = _build_git_fixture(tmp_path)
    v = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "require_new_commit": True,
            "op": "exists",
        }
    )
    assert v.verify(0).success is True


def test_require_new_commit_false_on_seed_only_repo(tmp_path):
    work = _init_repo(tmp_path)
    (work / "seed.txt").write_text("seed\n")
    _run(work, "add", "-A")
    _run(work, "commit", "-m", "seed")
    _run(work, "push", "-u", "origin", "main")

    v = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": str(work.parent / "origin.git"),
            "require_new_commit": True,
            "op": "exists",
        }
    )
    assert v.verify(0).success is False


def test_multidoc_ingress_apiversion_migrated(tmp_path):
    fixture = _build_git_fixture(tmp_path)
    v = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "file": "app.yaml",
            "path": "$[?(@.kind=='Ingress')].apiVersion",
            "op": "eq",
            "value": "networking.k8s.io/v1",
        }
    )
    assert v.verify(0).success is True


def test_multidoc_v1beta1_absent_on_fixed_present_on_seed(tmp_path):
    fixture = _build_git_fixture(tmp_path)
    spec = {
        "type": "git_repo_sync",
        "repo_path": fixture.bare,
        "file": "app.yaml",
        "path": "$[?(@.apiVersion=='networking.k8s.io/v1beta1')]",
        "op": "absent",
    }

    v_fixed = GitRepoSyncVerifier.model_validate(spec)
    assert v_fixed.verify(0).success is True

    v_seed = GitRepoSyncVerifier.model_validate({**spec, "ref": fixture.seed_sha})
    assert v_seed.verify(0).success is False


def test_quantifier_all_and_none_across_matches(tmp_path):
    fixture = _build_git_fixture(tmp_path)

    v_all = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "file": "app.yaml",
            "path": "$[*].kind",
            "op": "ne",
            "value": "ServiceAccount",
            "quantifier": "all",
        }
    )
    assert v_all.verify(0).success is True

    v_none_fails = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "file": "app.yaml",
            "path": "$[*].kind",
            "op": "ne",
            "value": "ServiceAccount",
            "quantifier": "none",
        }
    )
    assert v_none_fails.verify(0).success is False

    v_none_passes = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "file": "app.yaml",
            "path": "$[*].apiVersion",
            "op": "eq",
            "value": "banana",
            "quantifier": "none",
        }
    )
    assert v_none_passes.verify(0).success is True

    v_all_fails = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "file": "app.yaml",
            "path": "$[*].apiVersion",
            "op": "eq",
            "value": "banana",
            "quantifier": "all",
        }
    )
    assert v_all_fails.verify(0).success is False


def test_repo_path_nonexistent_dir_returns_false(tmp_path):
    v = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": str(tmp_path / "does-not-exist.git"),
            "op": "exists",
        }
    )
    assert v.verify(0).success is False


def test_file_not_found_at_ref_returns_false(tmp_path):
    fixture = _build_git_fixture(tmp_path)
    v = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "file": "workloads/does-not-exist.yaml",
            "op": "exists",
        }
    )
    assert v.verify(0).success is False


def test_absent_on_missing_file_is_true(tmp_path):
    fixture = _build_git_fixture(tmp_path)
    v = GitRepoSyncVerifier.model_validate(
        {
            "type": "git_repo_sync",
            "repo_path": fixture.bare,
            "file": "workloads/does-not-exist.yaml",
            "op": "absent",
        }
    )
    assert v.verify(0).success is True
