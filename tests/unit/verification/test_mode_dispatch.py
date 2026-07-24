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

"""Unit tests for per-entry mode dispatch (converge / assert / hold)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from devops_bench.tasks.schema import VerificationEntry
from devops_bench.verification import VerificationResult, VerificationSpec, VerifierAgent
from devops_bench.verification.rollup import EvaluatedEntry
from devops_bench.verification.verifiers import PodHealthyVerifier


def _stub(success: bool = True, reason: str = "ok") -> VerificationResult:
    return VerificationResult(success=success, elapsed_time=0.0, reason=reason)


def _entry(**over: Any) -> VerificationEntry:
    base = {
        "name": "e",
        "role": "objective",
        "check": {"type": "pod_healthy", "selector": "app=web"},
    }
    base.update(over)
    return VerificationEntry.model_validate(base)


def _node(entry: VerificationEntry) -> Any:
    return VerificationSpec(entry.check).root


def test_run_entry_returns_evaluated_entry():
    entry = _entry()
    with patch.object(PodHealthyVerifier, "verify", lambda self, t: _stub(True)):
        ev = VerifierAgent().run_entry(entry, _node(entry), timeout_sec=10)
    assert isinstance(ev, EvaluatedEntry)
    assert ev.name == "e"
    assert ev.role == "objective"
    assert ev.severity is None
    assert ev.weight == 1.0
    assert ev.result.success is True


def test_objective_defaults_to_converge_full_budget():
    seen: list[float] = []

    def fake(self: PodHealthyVerifier, timeout_sec: float) -> VerificationResult:
        seen.append(timeout_sec)
        return _stub(True)

    entry = _entry(role="objective")
    with patch.object(PodHealthyVerifier, "verify", fake):
        VerifierAgent().run_entry(entry, _node(entry), timeout_sec=30)
    # converge hands the leaf ~the full remaining budget.
    assert len(seen) == 1
    assert 25.0 < seen[0] <= 30.0


def test_safeguard_defaults_to_assert_single_shot():
    seen: list[float] = []

    def fake(self: PodHealthyVerifier, timeout_sec: float) -> VerificationResult:
        seen.append(timeout_sec)
        return _stub(True)

    entry = _entry(role="safeguard", severity="recoverable")
    with patch.object(PodHealthyVerifier, "verify", fake):
        VerifierAgent().run_entry(entry, _node(entry), timeout_sec=30)
    # assert evaluates exactly once with a zero budget (snapshot).
    assert seen == [0.0]


def test_explicit_mode_overrides_role_default():
    seen: list[float] = []

    def fake(self: PodHealthyVerifier, timeout_sec: float) -> VerificationResult:
        seen.append(timeout_sec)
        return _stub(True)

    # An objective forced to assert evaluates once at 0.0.
    entry = _entry(role="objective", mode="assert")
    with patch.object(PodHealthyVerifier, "verify", fake):
        VerifierAgent().run_entry(entry, _node(entry), timeout_sec=30)
    assert seen == [0.0]


def test_hold_samples_multiple_times_and_passes():
    calls = {"n": 0}

    def fake(self: PodHealthyVerifier, timeout_sec: float) -> VerificationResult:
        calls["n"] += 1
        return _stub(True)

    entry = _entry(
        role="safeguard",
        severity="recoverable",
        mode="hold",
        hold_window_sec=0.3,
        hold_poll_interval_sec=0.1,
    )
    with patch.object(PodHealthyVerifier, "verify", fake):
        ev = VerifierAgent().run_entry(entry, _node(entry), timeout_sec=30)
    assert ev.result.success is True
    assert calls["n"] >= 2  # sampled more than once across the window


def test_hold_fails_on_first_failing_sample():
    def fake(self: PodHealthyVerifier, timeout_sec: float) -> VerificationResult:
        return _stub(False, reason="dropped")

    entry = _entry(
        role="safeguard",
        severity="recoverable",
        mode="hold",
        hold_window_sec=0.3,
        hold_poll_interval_sec=0.1,
    )
    with patch.object(PodHealthyVerifier, "verify", fake):
        ev = VerifierAgent().run_entry(entry, _node(entry), timeout_sec=30)
    assert ev.result.success is False
    assert "hold failed" in ev.result.reason


def test_wait_for_condition_unchanged_converge_behavior():
    # The public chaos-path method must still hand the leaf ~the full budget.
    seen: list[float] = []

    def fake(self: PodHealthyVerifier, timeout_sec: float) -> VerificationResult:
        seen.append(timeout_sec)
        return _stub(True)

    spec = VerificationSpec({"type": "pod_healthy", "selector": "app=web"})
    with patch.object(PodHealthyVerifier, "verify", fake):
        VerifierAgent().wait_for_condition(spec, timeout_sec=30)
    assert len(seen) == 1
    assert 25.0 < seen[0] <= 30.0
