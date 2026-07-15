import subprocess
import time
from typing import Literal, Optional
from pkg.agents.verifier.base import BaseVerifier, VerificationResult


class ResourceExistsVerifier(BaseVerifier):
    """Verifies that a named Kubernetes resource exists in the cluster.

    Generic primitive over `kubectl get <kind> <name>`. Because it reads live
    cluster state, a successful check also proves the resource was actually
    applied (not merely printed by the agent).
    """

    type: Literal["resource_exists"] = "resource_exists"
    kind: str
    name: str
    namespace: Optional[str] = None

    def verify(self, timeout_sec: int) -> VerificationResult:
        start_time = time.time()
        delay = 1
        max_delay = 10

        while True:
            success, details = self._check_exists()
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

    def _check_exists(self) -> tuple[bool, dict]:
        cmd = ["kubectl", "get", self.kind, self.name]
        if self.namespace:
            cmd.extend(["-n", self.namespace])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, {
                "reason": f"{self.kind}/{self.name} exists",
                "output": result.stdout.strip(),
            }
        except subprocess.CalledProcessError as e:
            return False, {
                "reason": f"{self.kind}/{self.name} not found: {e.stderr.strip()}"
            }
