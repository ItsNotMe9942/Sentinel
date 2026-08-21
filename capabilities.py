from capability_registry import Capability, CapabilityRegistry
from state import EngagementState


def enumerate_http(state: EngagementState) -> None:
    print(f"[SIMULATED] Enumerating HTTP for target: {state.target}")


def review_observations(state: EngagementState) -> None:
    print(f"[SIMULATED] Reviewing {len(state.observations)} observation(s)")


def build_default_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()

    registry.register(
        Capability(
            name="enumerate_http",
            description="Simulate HTTP enumeration for the current target.",
            handler=enumerate_http,
        )
    )
    registry.register(
        Capability(
            name="review_observations",
            description="Simulate review of the current engagement observations.",
            handler=review_observations,
        )
    )

    return registry