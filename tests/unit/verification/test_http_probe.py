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

"""Unit tests for HttpProbeVerifier.

The subprocess run call is mocked throughout; no real cluster required.
"""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from devops_bench.core import SubprocessError
from devops_bench.verification.verifiers.http_probe import HttpProbeVerifier


def _completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


# -- basic success / failure --------------------------------------------------


def test_probe_succeeds_on_expected_status():
    response = "hello world\n200"
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        return_value=_completed(response),
    ):
        result = HttpProbeVerifier(url="http://svc/health").verify(timeout_sec=30)

    assert result.success is True
    assert "200" in result.reason
    assert result.raw["status_code"] == 200


def test_probe_fails_on_unexpected_status():
    response = "error page\n503"
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        return_value=_completed(response),
    ):
        result = HttpProbeVerifier(url="http://svc/health").verify(timeout_sec=30)

    assert result.success is False
    assert "503" in result.reason


def test_probe_fails_when_body_does_not_match():
    response = "not the pattern\n200"
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        return_value=_completed(response),
    ):
        result = HttpProbeVerifier(
            url="http://svc/health",
            expect_body_matches="healthy",
        ).verify(timeout_sec=30)

    assert result.success is False
    assert "body" in result.reason.lower()


def test_probe_succeeds_when_body_matches():
    response = '{"status": "healthy"}\n200'
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        return_value=_completed(response),
    ):
        result = HttpProbeVerifier(
            url="http://svc/health",
            expect_body_matches=r'"status":\s*"healthy"',
        ).verify(timeout_sec=30)

    assert result.success is True


def test_probe_uses_custom_expect_status():
    response = "created\n201"
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        return_value=_completed(response),
    ):
        result = HttpProbeVerifier(
            url="http://svc/items",
            expect_status=201,
        ).verify(timeout_sec=30)

    assert result.success is True


# -- subprocess failure -------------------------------------------------------


def test_probe_fails_on_subprocess_error():
    exc = SubprocessError(["kubectl", "run"], returncode=1, stdout="", stderr="timeout")
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        side_effect=exc,
    ):
        result = HttpProbeVerifier(url="http://svc/health").verify(timeout_sec=30)

    assert result.success is False
    assert "kubectl run failed" in result.reason
    assert "timeout" in result.reason


# -- malformed curl output ----------------------------------------------------


def test_probe_fails_on_unparseable_status():
    response = "output without status"
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        return_value=_completed(response),
    ):
        result = HttpProbeVerifier(url="http://svc/health").verify(timeout_sec=30)

    assert result.success is False


# -- kubectl command shape ----------------------------------------------------


def test_probe_command_includes_url_and_namespace():
    captured_argv: list[list[str]] = []

    def fake_run(argv, **kwargs):
        captured_argv.append(argv)
        return _completed("ok\n200")

    with patch("devops_bench.verification.verifiers.http_probe.run", fake_run):
        HttpProbeVerifier(
            url="http://backend/health",
            namespace="staging",
        ).verify(timeout_sec=30)

    argv = captured_argv[0]
    assert "kubectl" in argv
    assert "run" in argv
    assert "--rm" in argv
    assert "--restart=Never" in argv
    assert "-n" in argv
    assert "staging" in argv
    assert "http://backend/health" in argv
    assert "curlimages/curl" in " ".join(argv)


def test_probe_command_omits_namespace_when_not_set():
    captured_argv: list[list[str]] = []

    def fake_run(argv, **kwargs):
        captured_argv.append(argv)
        return _completed("ok\n200")

    with patch("devops_bench.verification.verifiers.http_probe.run", fake_run):
        HttpProbeVerifier(url="http://svc/health").verify(timeout_sec=30)

    argv = captured_argv[0]
    assert "-n" not in argv


# -- result metadata ----------------------------------------------------------


def test_probe_echoes_weight_onto_result():
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        return_value=_completed("ok\n200"),
    ):
        result = HttpProbeVerifier(url="http://svc/health", weight=2.5).verify(timeout_sec=30)

    assert result.weight == 2.5


def test_probe_echoes_name_onto_result():
    with patch(
        "devops_bench.verification.verifiers.http_probe.run",
        return_value=_completed("ok\n200"),
    ):
        result = HttpProbeVerifier(url="http://svc/health", name="liveness").verify(timeout_sec=30)

    assert result.name == "liveness"


# -- registry registration ----------------------------------------------------


def test_http_probe_is_registered():
    from devops_bench.verification.base import VERIFIERS

    assert "http_probe" in VERIFIERS
