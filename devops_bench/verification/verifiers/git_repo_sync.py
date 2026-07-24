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

"""Verifier that asserts a property of a file or the commit state in a host-side git repo."""

from __future__ import annotations

import os
from typing import Any, Literal

import yaml
from jsonpath_ng.exceptions import JSONPathError
from jsonpath_ng.ext import parse as jsonpath_parse
from pydantic import PrivateAttr, model_validator

from devops_bench.core import SubprocessError, get_logger
from devops_bench.core.subprocess import run
from devops_bench.verification.base import VERIFIERS, BaseVerifier, VerificationResult
from devops_bench.verification.verifiers.resource_property import (
    _SCALAR_OPS,
    _eval_op,
    _Op,
    _Quantifier,
)

__all__ = ["GitRepoSyncVerifier"]

_log = get_logger("verification.git_repo_sync")


@VERIFIERS.register("git_repo_sync")
class GitRepoSyncVerifier(BaseVerifier):
    """Assert a property of a file at a git ref, or that a new commit was made, in a bare repo.

    Reads a host-side bare repo directly (no clone) with ``git -C <repo> show
    <ref>:<file>``. ``file`` content is parsed as one or more YAML documents and
    ``path`` (JSONPath, extended) is evaluated against the list of documents, so
    a filter predicate selects the right doc in a multi-document manifest. Scalar
    ops reuse resource_property's ``_eval_op`` (quantity-aware). ``require_new_commit``
    asserts HEAD is past the repo's root (seed) commit, so a no-op agent fails.

    Attributes:
        type: Discriminator literal, always ``"git_repo_sync"``.
        repo_path: Path to the bare repo (``~`` is expanded).
        ref: Git ref to read; default ``"HEAD"``.
        file: Path of a file within the repo tree; content read at ``ref``.
        path: Optional JSONPath into the file's YAML documents (a list).
        op: Comparison operator (resource_property's vocabulary).
        value: Expected value for comparison ops.
        quantifier: all/any/none across matched documents; default all.
        require_new_commit: Also require HEAD to be past the root (seed) commit.
    """

    type: Literal["git_repo_sync"] = "git_repo_sync"
    repo_path: str
    ref: str = "HEAD"
    file: str | None = None
    path: str | None = None
    op: _Op
    value: Any = None
    quantifier: _Quantifier = "all"
    require_new_commit: bool = False

    _compiled: Any = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _validate(self) -> GitRepoSyncVerifier:
        """Expand ``~`` in ``repo_path``, enforce ``file``/``path`` prerequisites, compile JSONPath."""
        self.repo_path = os.path.expanduser(self.repo_path)
        if self.op in _SCALAR_OPS and self.path is None and self.file is None:
            raise ValueError(f"op {self.op!r} requires a 'file' (and usually a 'path')")
        if self.path is not None and self.file is None:
            raise ValueError("'path' requires a 'file' to read from the repo")
        if self.path is not None:
            try:
                self._compiled = jsonpath_parse(self.path)
            except JSONPathError as exc:
                raise ValueError(f"invalid JSONPath {self.path!r}: {exc}") from exc
        return self

    def verify(self, timeout_sec: float) -> VerificationResult:
        """Poll the git assertion to a result (converge/assert/hold aware)."""
        return self._poll_to_result(self._check, timeout_sec)

    def _git(self, *args: str) -> str:
        return run(["git", "-C", self.repo_path, *args]).stdout

    def _check(self) -> tuple[bool, str, dict[str, Any] | None]:
        """Resolve ``ref``, optionally check for a new commit, then evaluate the file/path/op."""
        try:
            head = self._git("rev-parse", self.ref).strip()
        except SubprocessError as exc:
            return (
                False,
                f"git ref not resolvable at {self.repo_path}:{self.ref}: "
                f"{(exc.stderr or '').strip()}",
                None,
            )
        except Exception as exc:  # noqa: BLE001 - retryable failure, never raise
            return False, f"unexpected git error: {exc}", None

        if self.require_new_commit:
            try:
                roots = self._git("rev-list", "--max-parents=0", self.ref).split()
            except SubprocessError:
                roots = []
            if head in roots:
                return False, f"no new commit since the seed root ({head[:8]})", None

        if self.file is None:
            if self.op == "absent":
                return False, f"repo ref present at {self.ref} (absent not satisfied)", {"sha": head}
            return True, f"repo at {self.ref} ({head[:8]})", {"sha": head}

        try:
            content = self._git("show", f"{self.ref}:{self.file}")
        except SubprocessError as exc:
            if self.op == "absent" and self.path is None:
                return True, f"{self.file} absent at {self.ref}", {"sha": head}
            return (
                False,
                f"{self.file} not found at {self.ref}: {(exc.stderr or '').strip()}",
                {"sha": head},
            )

        if self.path is None:
            if self.op == "exists":
                return True, f"{self.file} exists at {self.ref}", {"sha": head}
            if self.op == "absent":
                return False, f"{self.file} present at {self.ref}", {"sha": head}
            ok = _eval_op(content, self.op, self.value)
            return ok, f"{self.file} {self.op} {self.value!r} -> {ok}", {"sha": head}

        try:
            docs = [d for d in yaml.safe_load_all(content) if d is not None]
        except yaml.YAMLError as exc:
            return False, f"failed to parse YAML in {self.file}: {exc}", {"sha": head}

        matches = self._compiled.find(docs)
        if self.op == "exists":
            return (
                (len(matches) > 0),
                f"path {self.path!r} {'exists' if matches else 'not found'} in {self.file}",
                {"sha": head},
            )
        if self.op == "absent":
            return (
                (len(matches) == 0),
                f"path {self.path!r} {'absent' if not matches else 'present'} in {self.file}",
                {"sha": head},
            )
        if not matches:
            return False, f"path {self.path!r} not found in {self.file}", {"sha": head}
        results = [_eval_op(m.value, self.op, self.value) for m in matches]
        passed = sum(1 for r in results if r)
        total = len(results)
        if self.quantifier == "all":
            ok = passed == total
        elif self.quantifier == "any":
            ok = passed > 0
        else:
            ok = passed == 0
        raw = {"sha": head, "objects_checked": total, "passed": passed}
        return (
            ok,
            f"{self.file} {self.quantifier}: {passed}/{total} for {self.path}={self.op} "
            f"{self.value!r}",
            raw,
        )
