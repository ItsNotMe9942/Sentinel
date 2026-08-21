from collections.abc import Callable
from dataclasses import dataclass

from state import EngagementState


CapabilityHandler = Callable[[EngagementState], None]


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    handler: CapabilityHandler

    def execute(self, state: EngagementState) -> None:
        self.handler(state)


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(f"Capability already registered: {capability.name}")

        self._capabilities[capability.name] = capability

    def resolve(self, name: str) -> Capability:
        try:
            return self._capabilities[name]
        except KeyError as error:
            raise KeyError(f"Capability not registered: {name}") from error