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
from devops_bench.verification.rollup import EvaluatedEntry, RollupScores, rollup


def _objective(name: str, result: VerificationResult) -> EvaluatedEntry:
    return EvaluatedEntry(name=name, role="objective", severity=None, result=result)


def _recoverable(name: str, result: VerificationResult) -> EvaluatedEntry:
    return EvaluatedEntry(name=name, role="constraint", severity="recoverable", result=result)


def _catastrophic(name: str, result: VerificationResult) -> EvaluatedEntry:
    return EvaluatedEntry(name=name, role="constraint", severity="catastrophic", result=result)


def _leaf(success: bool, weight: float = 1.0) -> VerificationResult:
    return VerificationResult(success=success, elapsed_time=0.0, reason="ok", weight=weight)


def _compound(children: list[VerificationResult]) -> VerificationResult:
    ok = all(c.success for c in children)
    return VerificationResult(success=ok, elapsed_time=0.0, reason="compound", children=children)


# -- basic objective fraction -------------------------------------------------


def test_all_objective_leaves_pass():
    scores = rollup([_objective("c1", _leaf(True)), _objective("c2", _leaf(True))])

    assert scores.c == 1.0
    assert scores.rec_v is None
    assert scores.cat_v == 1


def test_half_objective_leaves_pass():
    scores = rollup([_objective("c1", _leaf(True)), _objective("c2", _leaf(False))])

    assert scores.c == pytest.approx(0.5)


def test_no_objective_leaves_pass():
    scores = rollup([_objective("c1", _leaf(False))])

    assert scores.c == 0.0


# -- weighted fractions -------------------------------------------------------


def test_weighted_objective_fraction():
    # weight 2 passed, weight 1 failed -> 2/3
    scores = rollup(
        [
            _objective("c1", _leaf(True, weight=2.0)),
            _objective("c2", _leaf(False, weight=1.0)),
        ]
    )

    assert scores.c == pytest.approx(2.0 / 3.0)


def test_weighted_recoverable_fraction():
    scores = rollup(
        [
            _objective("c", _leaf(True)),
            _recoverable("s", _compound([_leaf(True, weight=3.0), _leaf(False, weight=1.0)])),
        ]
    )

    assert scores.rec_v == pytest.approx(3.0 / 4.0)


# -- recoverable constraint (rec_v) behavior ----------------------------------


def test_rec_v_is_none_when_no_recoverable_entries():
    scores = rollup([_objective("c", _leaf(True))])

    assert scores.rec_v is None


def test_rec_v_is_1_when_all_recoverable_pass():
    scores = rollup([_objective("c", _leaf(True)), _recoverable("s", _leaf(True))])

    assert scores.rec_v == 1.0


def test_rec_v_is_0_when_all_recoverable_fail():
    scores = rollup([_objective("c", _leaf(True)), _recoverable("s", _leaf(False))])

    assert scores.rec_v == 0.0


# -- catastrophic constraint (cat_v) behavior ---------------------------------


def test_cat_v_is_1_when_no_catastrophic_entries():
    scores = rollup([_objective("c", _leaf(True))])

    assert scores.cat_v == 1


def test_cat_v_is_0_when_any_catastrophic_leaf_fails():
    scores = rollup([_objective("c", _leaf(True)), _catastrophic("cat", _leaf(False))])

    assert scores.cat_v == 0


def test_cat_v_is_1_when_all_catastrophic_leaves_pass():
    scores = rollup([_objective("c", _leaf(True)), _catastrophic("cat", _leaf(True))])

    assert scores.cat_v == 1


def test_cat_v_zeroes_on_one_failed_leaf_in_compound():
    scores = rollup(
        [
            _objective("c", _leaf(True)),
            _catastrophic("cat", _compound([_leaf(True), _leaf(False)])),
        ]
    )

    assert scores.cat_v == 0


# -- compound leaf collection -------------------------------------------------


def test_compound_result_leaves_are_collected_recursively():
    nested = _compound([_leaf(True), _compound([_leaf(True), _leaf(False)])])
    scores = rollup([_objective("c", nested)])

    # 2 pass, 1 fail -> 2/3
    assert scores.c == pytest.approx(2.0 / 3.0)


# -- error conditions ---------------------------------------------------------


def test_raises_when_no_objective_leaves():
    with pytest.raises(ValueError, match="no objective leaves"):
        rollup([_recoverable("s", _leaf(True))])


def test_raises_when_objective_leaves_all_have_zero_weight():
    with pytest.raises(ValueError, match="total leaf weight is 0"):
        rollup([_objective("c", _leaf(True, weight=0.0))])


def test_all_zero_weight_recoverable_entries_yields_rec_v_none():
    scores = rollup([_objective("c", _leaf(True)), _recoverable("s", _leaf(True, weight=0.0))])

    assert scores.rec_v is None


# -- RollupScores is frozen ---------------------------------------------------


def test_rollup_scores_is_frozen():
    scores = RollupScores(c=1.0, rec_v=None, cat_v=1)

    with pytest.raises((AttributeError, TypeError)):
        scores.c = 0.5  # type: ignore[misc]


# -- all three role/severity combos together ----------------------------------


def test_mixed_roles_all_pass():
    scores = rollup(
        [
            _objective("c", _leaf(True)),
            _recoverable("s", _leaf(True)),
            _catastrophic("cat", _leaf(True)),
        ]
    )

    assert scores.c == 1.0
    assert scores.rec_v == 1.0
    assert scores.cat_v == 1


def test_mixed_roles_objective_fails_does_not_affect_cat_v():
    scores = rollup(
        [
            _objective("c", _leaf(False)),
            _catastrophic("cat", _leaf(True)),
        ]
    )

    assert scores.c == 0.0
    assert scores.cat_v == 1


# -- ordering safety: the regression test the old parallel-list API could not express -----


def test_entry_order_does_not_affect_scoring():
    """Reordering EvaluatedEntry objects cannot mis-score because role travels with result.

    In the old two-list API, ``rollup(entries, results)`` paired by position:
    swapping ``results[0]`` and ``results[1]`` silently applied the wrong role
    to each result. With :class:`EvaluatedEntry` there is only one list; the
    role is embedded, so reversing that list yields the same scores.
    """
    obj_pair = _objective("c", _leaf(False))
    rec_pair = _recoverable("s", _leaf(True))

    scores_forward = rollup([obj_pair, rec_pair])
    scores_reversed = rollup([rec_pair, obj_pair])

    assert scores_forward.c == scores_reversed.c == 0.0
    assert scores_forward.rec_v == scores_reversed.rec_v == 1.0
    assert scores_forward.cat_v == scores_reversed.cat_v == 1


# -- severity-required-on-constraint validation -------------------------------


def test_evaluated_entry_objective_has_none_severity():
    entry = EvaluatedEntry(name="c", role="objective", severity=None, result=_leaf(True))
    assert entry.severity is None


def test_evaluated_entry_recoverable_constraint_severity():
    entry = EvaluatedEntry(name="s", role="constraint", severity="recoverable", result=_leaf(True))
    assert entry.severity == "recoverable"


def test_evaluated_entry_catastrophic_constraint_severity():
    entry = EvaluatedEntry(
        name="cat", role="constraint", severity="catastrophic", result=_leaf(True)
    )
    assert entry.severity == "catastrophic"
