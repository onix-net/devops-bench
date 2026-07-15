import subprocess
import time
from typing import Literal, Optional
from pkg.agents.verifier.base import BaseVerifier, VerificationResult


class ResourceFieldVerifier(BaseVerifier):
    """Verifies that a specific field on a Kubernetes resource equals an
    expected value.

    Generic primitive over `kubectl get <kind> <name> -o jsonpath=<json_path>`.
    kubectl performs the extraction, so no extra Python dependency is required.
    Reading the live field value also proves the resource was actually applied
    with the correct configuration.

    Example (container env var):
        json_path = "{.spec.template.spec.containers[?(@.name=='frontend')]"
                    ".env[?(@.name=='USE_GEMINI_API')].value}"
        expected  = "false"
    """

    type: Literal["resource_field"] = "resource_field"
    kind: str
    name: str
    json_path: str
    expected: str
    namespace: Optional[str] = None

    def verify(self, timeout_sec: int) -> VerificationResult:
        start_time = time.time()
        delay = 1
        max_delay = 10

        while True:
            success, details = self._check_field()
            if success:
                return VerificationResult(
                    success=True,
                    elapsed_time=time.time() - start_time,
                    reason=details.get("reason"),
                    details=details,
                )
            if time.time() - start_time >= timeout_sec:
                return VerificationResult(
                    success=False,
                    elapsed_time=time.time() - start_time,
                    reason=details.get("reason"),
                    details=details,
                )
            time.sleep(delay)
            delay = min(delay * 2, max_delay)

    def _check_field(self) -> (bool, dict):
        cmd = [
            "kubectl",
            "get",
            self.kind,
            self.name,
            "-o",
            f"jsonpath={self.json_path}",
        ]
        if self.namespace:
            cmd.extend(["-n", self.namespace])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return False, {
                "reason": f"Failed to read {self.kind}/{self.name}: {e.stderr.strip()}"
            }

        actual = result.stdout.strip()
        success = actual == self.expected
        reason = (
            f"{self.kind}/{self.name} field matched expected value '{self.expected}'"
            if success
            else (
                f"{self.kind}/{self.name} field mismatch: expected "
                f"'{self.expected}', got '{actual}'"
            )
        )
        return success, {
            "reason": reason,
            "json_path": self.json_path,
            "expected": self.expected,
            "actual": actual,
        }
