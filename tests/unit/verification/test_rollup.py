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

"""Unit tests for the verification rollup module."""

from __future__ import annotations

import pytest

from devops_bench.verification.base import VerificationResult
from devops_bench.verification.entry import VerificationEntry
from devops_bench.verification.rollup import RollupScores, rollup


def _entry(name: str, role: str = "correctness") -> VerificationEntry:
    return VerificationEntry(name=name, role=role, spec={})


def _leaf(success: bool, weight: float = 1.0) -> VerificationResult:
    return VerificationResult(success=success, elapsed_time=0.0, reason="ok", weight=weight)


def _compound(children: list[VerificationResult]) -> VerificationResult:
    ok = all(c.success for c in children)
    return VerificationResult(success=ok, elapsed_time=0.0, reason="compound", children=children)


# -- basic correctness fraction -----------------------------------------------


def test_all_correctness_leaves_pass():
    entries = [_entry("c1"), _entry("c2")]
    results = [_leaf(True), _leaf(True)]

    scores = rollup(entries, results)

    assert scores.c == 1.0
    assert scores.rec_v is None
    assert scores.cat_v == 1


def test_half_correctness_leaves_pass():
    entries = [_entry("c1"), _entry("c2")]
    results = [_leaf(True), _leaf(False)]

    scores = rollup(entries, results)

    assert scores.c == pytest.approx(0.5)


def test_no_correctness_leaves_pass():
    entries = [_entry("c1")]
    results = [_leaf(False)]

    scores = rollup(entries, results)

    assert scores.c == 0.0


# -- weighted fractions -------------------------------------------------------


def test_weighted_correctness_fraction():
    entries = [_entry("c1"), _entry("c2")]
    # weight 2 passed, weight 1 failed -> 2/3
    results = [_leaf(True, weight=2.0), _leaf(False, weight=1.0)]

    scores = rollup(entries, results)

    assert scores.c == pytest.approx(2.0 / 3.0)


def test_weighted_safety_fraction():
    entries = [_entry("c"), _entry("s", role="safety")]
    results = [_leaf(True), _compound([_leaf(True, weight=3.0), _leaf(False, weight=1.0)])]

    scores = rollup(entries, results)

    assert scores.rec_v == pytest.approx(3.0 / 4.0)


# -- safety (rec_v) behavior --------------------------------------------------


def test_rec_v_is_none_when_no_safety_entries():
    entries = [_entry("c")]
    results = [_leaf(True)]

    scores = rollup(entries, results)

    assert scores.rec_v is None


def test_rec_v_is_1_when_all_safety_pass():
    entries = [_entry("c"), _entry("s", role="safety")]
    results = [_leaf(True), _leaf(True)]

    scores = rollup(entries, results)

    assert scores.rec_v == 1.0


def test_rec_v_is_0_when_all_safety_fail():
    entries = [_entry("c"), _entry("s", role="safety")]
    results = [_leaf(True), _leaf(False)]

    scores = rollup(entries, results)

    assert scores.rec_v == 0.0


# -- catastrophic (cat_v) behavior --------------------------------------------


def test_cat_v_is_1_when_no_catastrophic_entries():
    entries = [_entry("c")]
    results = [_leaf(True)]

    scores = rollup(entries, results)

    assert scores.cat_v == 1


def test_cat_v_is_0_when_any_catastrophic_leaf_fails():
    entries = [_entry("c"), _entry("cat", role="catastrophic")]
    results = [_leaf(True), _leaf(False)]

    scores = rollup(entries, results)

    assert scores.cat_v == 0


def test_cat_v_is_1_when_all_catastrophic_leaves_pass():
    entries = [_entry("c"), _entry("cat", role="catastrophic")]
    results = [_leaf(True), _leaf(True)]

    scores = rollup(entries, results)

    assert scores.cat_v == 1


def test_cat_v_zeroes_on_one_failed_leaf_in_compound():
    entries = [_entry("c"), _entry("cat", role="catastrophic")]
    results = [_leaf(True), _compound([_leaf(True), _leaf(False)])]

    scores = rollup(entries, results)

    assert scores.cat_v == 0


# -- compound leaf collection -------------------------------------------------


def test_compound_result_leaves_are_collected_recursively():
    entries = [_entry("c")]
    nested = _compound([_leaf(True), _compound([_leaf(True), _leaf(False)])])
    results = [nested]

    scores = rollup(entries, results)

    # 2 pass, 1 fail -> 2/3
    assert scores.c == pytest.approx(2.0 / 3.0)


# -- error conditions ---------------------------------------------------------


def test_raises_when_no_correctness_leaves():
    entries = [_entry("s", role="safety")]
    results = [_leaf(True)]

    with pytest.raises(ValueError, match="no correctness leaves"):
        rollup(entries, results)


def test_raises_when_lengths_differ():
    entries = [_entry("c")]
    results = [_leaf(True), _leaf(True)]

    with pytest.raises(ValueError, match="same length"):
        rollup(entries, results)


# -- RollupScores is frozen ---------------------------------------------------


def test_rollup_scores_is_frozen():
    scores = RollupScores(c=1.0, rec_v=None, cat_v=1)

    with pytest.raises((AttributeError, TypeError)):
        scores.c = 0.5  # type: ignore[misc]


# -- all three roles together -------------------------------------------------


def test_mixed_roles_all_pass():
    entries = [
        _entry("c", "correctness"),
        _entry("s", "safety"),
        _entry("cat", "catastrophic"),
    ]
    results = [_leaf(True), _leaf(True), _leaf(True)]

    scores = rollup(entries, results)

    assert scores.c == 1.0
    assert scores.rec_v == 1.0
    assert scores.cat_v == 1


def test_mixed_roles_correctness_fails_does_not_affect_cat_v():
    entries = [
        _entry("c", "correctness"),
        _entry("cat", "catastrophic"),
    ]
    results = [_leaf(False), _leaf(True)]

    scores = rollup(entries, results)

    assert scores.c == 0.0
    assert scores.cat_v == 1
