from typing import Dict, List, Union
from pydantic import RootModel
from pkg.agents.verifier.pod_healthy import PodHealthyVerifier
from pkg.agents.verifier.scaling_complete import ScalingCompleteVerifier
from pkg.agents.verifier.resource_exists import ResourceExistsVerifier
from pkg.agents.verifier.resource_field import ResourceFieldVerifier

# SingleVerificationSpec is a discriminated union of all supported checker types
SingleVerificationSpec = Union[
    PodHealthyVerifier,
    ScalingCompleteVerifier,
    ResourceExistsVerifier,
    ResourceFieldVerifier,
]

# Top-level VerificationSpec which can parse a dict, a list, or a single checker spec.
class VerificationSpec(RootModel[Union[Dict[str, SingleVerificationSpec], List[SingleVerificationSpec], SingleVerificationSpec]]):
    """Represents a structured verification specification."""
    pass
